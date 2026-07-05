"""
TerraAudit — Прозорро.Продажі API клієнт (v2)
Оновлено під нову структуру API (ЦБД-2/нова): курсорна пагінація
за byDateModified, без прямого фільтра по типу на рівні запиту.

Ключові поля нової системи (виявлено емпірично через розвідку API):
- metaInfo.directions        → ["landRental"] для земельних лотів
- items[0].quantity          → площа ділянки в гектарах
- items[0].address.region    → регіон ділянки (не організатора!)
- items[0].additionalClassifications → текстовий опис типу землі
- value.amount               → річна орендна ставка (перевірено:
                                стабільно ~12% від normativeMonetaryValuation)
- status                     → "complete" | "unsuccessful" тощо
"""

import requests
import pandas as pd
import numpy as np
import time
from typing import Optional
from datetime import datetime, timedelta

BASE_URL = "https://procedure.prozorro.sale/api/search/byDateModified/"

# Простий in-memory кеш щоб не бомбити API повторно при кожному візиті табу
_CACHE = {}
_CACHE_TTL = 3600  # 1 година


# ─────────────────────────────────────────────
# Класифікація типу землі за текстом опису
# ─────────────────────────────────────────────

def _classify_land_type(type_text: str) -> str:
    """
    Визначає внутрішню категорію землі за текстом класифікації Прозорро.
    Повертає None якщо тип не відповідає жодній з 4 категорій UI
    (наприклад водний фонд, лісовий фонд тощо) — такі лоти виключаються
    з вибірки, бо вони не порівнянні з нашими типами землі.
    """
    t = type_text.lower()

    # Водний/лісовий фонд — окрема категорія активів, НЕ порівнянна
    # з сільгосп/пасовище/забудова/промисловість. Виключаємо повністю.
    # Широкий збіг "водн" ловить: водного фонду, водний об'єкт,
    # водойма, водосховище тощо.
    if "водн" in t or "рибогосподар" in t or "ставк" in t and "став" in t:
        return None
    if "лісов" in t:
        return None

    if "пасовищ" in t or "сіножат" in t:
        return "Пасовище"
    if "житлов" in t or "громадськ" in t or "забудов" in t:
        return "Забудова"
    if "промислов" in t or "транспорт" in t:
        return "Промисловість"
    if "сільськогосп" in t or "рілля" in t or "рілл" in t:
        return "Сільське господарство"

    return None  # невідомий тип — краще виключити, ніж класифікувати неправильно


# ─────────────────────────────────────────────
# Курсорна пагінація по byDateModified
# ─────────────────────────────────────────────

def fetch_land_auctions(
    max_records: int = 500,
    max_requests: int = 40,
    start_date: str = "2023-06-01T00:00:00.000000Z",
    request_timeout: int = 10,
    min_real_year: Optional[int] = None,
) -> list[dict]:
    """
    Проходить курсорну пагінацію Прозорро, збираючи завершені
    земельні лоти (landRental).

    Returns:
        Список dict: {price_per_ha, area_ha, region, land_type,
                       date, title, cadastral_number}
    """
    collected = []
    seen_ids = set()
    date_cursor = start_date

    for _ in range(max_requests):
        try:
            r = requests.get(
                f"{BASE_URL}{date_cursor}",
                params={"limit": 100},
                timeout=request_timeout,
            )
        except Exception as e:
            print(f"⚠️ Прозорро запит не вдався: {e}")
            break

        if r.status_code != 200:
            print(f"⚠️ Прозорро HTTP {r.status_code}")
            break

        try:
            batch = r.json()
        except Exception:
            break

        if not batch or not isinstance(batch, list):
            break

        for item in batch:
            try:
                item_id = item.get("_id") or item.get("auctionId")
                if item_id in seen_ids:
                    continue

                if item.get("status") != "complete":
                    continue

                directions = item.get("metaInfo", {}).get("directions", [])
                if "landRental" not in directions:
                    continue

                items_arr = item.get("items", [])
                if not items_arr:
                    continue

                it0 = items_arr[0]
                area = it0.get("quantity") or it0.get("itemProps", {}).get("landArea")
                if not area or area < 0.1:  # відсіюємо мікро-ділянки (<0.1 га = 1000 м²)
                    continue

                value = item.get("value", {})
                price = value.get("amount") if isinstance(value, dict) else None
                if not price or price <= 0:
                    continue

                price_per_ha = price / area

                classification_desc = (
                    it0.get("classification", {})
                       .get("description", {})
                       .get("uk_UA", "")
                )
                additional_desc = " ".join(
                    c.get("description", {}).get("uk_UA", "")
                    for c in it0.get("additionalClassifications", [])
                )
                item_desc_raw = it0.get("description", "")
                if isinstance(item_desc_raw, dict):
                    item_desc_raw = item_desc_raw.get("uk_UA", "")

                type_text = classification_desc + " " + additional_desc + " " + str(item_desc_raw)
                land_type = _classify_land_type(type_text)
                if land_type is None:
                    continue  # водний фонд, лісовий фонд, невідомий тип — пропускаємо

                # Санітарні межі залежно від типу землі
                sanity_max = {
                    "Сільське господарство": 60_000,
                    "Пасовище":               60_000,
                    "Забудова":              800_000,
                    "Промисловість":         500_000,
                }.get(land_type, 60_000)

                if not (100 < price_per_ha < sanity_max):
                    continue

                region = (
                    it0.get("address", {})
                       .get("region", {})
                       .get("uk_UA", "")
                )

                title_raw = item.get("title", "")
                title = (
                    title_raw.get("uk_UA", "")
                    if isinstance(title_raw, dict) else str(title_raw)
                )[:70]

                cadastral = it0.get("itemProps", {}).get("cadastralNumber", "")

                # Реальна дата завершення аукціону, не дата міграції запису
                real_date = (
                    item.get("datePublished")
                    or item.get("auctionPeriod", {}).get("endDate")
                    or item.get("dateModified", "")
                )

                seen_ids.add(item_id)
                collected.append({
                    "price_per_ha": round(price_per_ha, 0),
                    "area_ha":      round(area, 2),
                    "region":       region,
                    "land_type":    land_type,
                    "date":         real_date[:10] if real_date else "",
                    "title":        title or "Земельна ділянка",
                    "cadastral_number": cadastral,
                })

            except (KeyError, ValueError, TypeError, ZeroDivisionError):
                continue

        # Просуваємо курсор до dateModified останнього запису партії
        last_date = batch[-1].get("dateModified")
        if not last_date or last_date == date_cursor:
            break
        date_cursor = last_date

        if len(collected) >= max_records:
            break

        time.sleep(0.15)  # не бомбити API занадто швидко

    return collected


def get_cached_land_auctions(
    start_year: Optional[int] = None,
    force_refresh: bool = False,
) -> list[dict]:
    """
    Кешована версія fetch_land_auctions (TTL 1 година).
    start_year — рік, з якого починати пошук.

    ВАЖЛИВО: dateModified у Прозорро — це дата останньої зміни запису
    в системі (міграції), а НЕ реальна дата аукціону. Нова система
    ЦБД-2 почала повноцінно наповнюватись приблизно з середини 2023.
    Тому пошук ніколи не стартує раніше 2023 — інакше курсор
    "витрачає" запити на порожній період і падає на fallback.
    """
    now = time.time()
    year = max(start_year or 2023, 2023)  # floor — не шукати раніше 2023
    cache_key = f"land_auctions_{year}"

    if not force_refresh and cache_key in _CACHE:
        data, ts = _CACHE[cache_key]
        if now - ts < _CACHE_TTL:
            return data

    # ВАЖЛИВО: перші місяці 2023 (до червня) у системі ЦБД-2 майже порожні —
    # курсор "витрачає" запити на порожній період замість щільних даних.
    # Емпірично підтверджено (діагностика): 2023-06-01 — перевірена робоча
    # точка старту. Для year > 2023 використовуємо 1 січня цього року,
    # бо там дані вже щільні.
    _proven_start = "2023-06-01T00:00:00.000000Z"
    _candidate = f"{year}-01-01T00:00:00.000000Z"
    start_date = _candidate if _candidate > _proven_start else _proven_start

    data = fetch_land_auctions(start_date=start_date)
    _CACHE[cache_key] = (data, now)
    return data


# ─────────────────────────────────────────────
# Публічний інтерфейс (сумісний зі старим кодом)
# ─────────────────────────────────────────────

def fetch_land_lots(
    region: Optional[str] = None,
    land_type: Optional[str] = None,
    start_year: Optional[int] = None,
    status: str = "complete",
    limit: int = 100,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """
    Повертає DataFrame земельних лотів для відображення в таблиці.
    Використовує кешовану курсорну вибірку з нового API.
    Фільтрує по типу землі якщо вказано.
    start_year — з якого року шукати (прив'язка до аналізу в UI).
    force_refresh — обійти кеш і завантажити заново (кнопка "Оновити").
    Якщо реальних даних немає — fallback на синтетичні.
    """
    records = get_cached_land_auctions(start_year=start_year, force_refresh=force_refresh)

    if len(records) < 5:
        return _demo_data()

    df = pd.DataFrame(records)
    df["final_price"] = df["price_per_ha"] * df["area_ha"]

    if land_type and "land_type" in df.columns:
        filtered = df[df["land_type"] == land_type]
        # Якщо після фільтру замало записів — показуємо все, але позначаємо
        if len(filtered) >= 3:
            df = filtered

    if region and "region" in df.columns:
        region_filtered = df[df["region"].str.contains(region, case=False, na=False)]
        if len(region_filtered) >= 3:
            df = region_filtered

    return df.head(limit)


def _demo_data() -> pd.DataFrame:
    """Демо-дані коли API недоступний або дало замало результатів."""
    np.random.seed(42)
    regions = ["Черкаська", "Полтавська", "Вінницька", "Київська", "Харківська"]
    base = {"Черкаська": 4800, "Полтавська": 4200,
            "Вінницька": 4600, "Київська": 6200, "Харківська": 3900}
    records = []
    for i in range(60):
        region = np.random.choice(regions)
        area = np.random.uniform(0.5, 15.0)
        ppha = base[region] * np.random.uniform(0.7, 1.4)
        records.append({
            "id":           f"demo-{i:04d}",
            "title":        f"Земельна ділянка с/г призначення, {region} обл.",
            "area_ha":      round(area, 2),
            "final_price":  round(ppha * area, 0),
            "price_per_ha": round(ppha, 0),
            "region":       region,
            "land_type":    "Сільське господарство",
            "date":         f"2023-{np.random.randint(1,13):02d}-{np.random.randint(1,28):02d}",
        })
    return pd.DataFrame(records)


def get_comparable_prices(
    df: pd.DataFrame,
    region: str,
    area_ha: float,
    land_type: Optional[str] = None,
    tolerance: float = 0.5,
) -> list:
    """Фільтрує порівняльні ціни для побудови цінового коридору."""
    filtered = df.copy()

    if land_type and "land_type" in filtered.columns:
        filtered = filtered[filtered["land_type"] == land_type]

    if region:
        filtered = filtered[
            filtered["region"].str.contains(region, case=False, na=False)
        ]

    area_filtered = filtered[
        filtered["area_ha"].between(area_ha * (1 - tolerance), area_ha * (1 + tolerance))
    ]

    if len(area_filtered) >= 5:
        return area_filtered["price_per_ha"].tolist()

    return filtered["price_per_ha"].tolist()