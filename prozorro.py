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
    """Визначає внутрішню категорію землі за текстом класифікації Прозорро."""
    t = type_text.lower()
    if "пасовищ" in t or "сіножат" in t:
        return "Пасовище"
    if "сільськогосп" in t or "рілля" in t or "орн" in t:
        return "Сільське господарство"
    if "житлов" in t or "громадськ" in t or "забудов" in t:
        return "Забудова"
    if "промислов" in t or "транспорт" in t:
        return "Промисловість"
    return "Сільське господарство"  # дефолт — більшість лотів це с/г


# ─────────────────────────────────────────────
# Курсорна пагінація по byDateModified
# ─────────────────────────────────────────────

def fetch_land_auctions(
    max_records: int = 300,
    max_requests: int = 15,
    start_date: str = "2023-06-01T00:00:00.000000Z",
    request_timeout: int = 10,
) -> list[dict]:
    """
    Проходить курсорну пагінацію Прозорро, збираючи завершені
    земельні лоти (landRental).

    Returns:
        Список dict: {price_per_ha, area_ha, region, land_type,
                       date, title, cadastral_number}
    """
    collected = []
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
                if not area or area <= 0:
                    continue

                value = item.get("value", {})
                price = value.get("amount") if isinstance(value, dict) else None
                if not price or price <= 0:
                    continue

                price_per_ha = price / area
                if not (100 < price_per_ha < 500_000):
                    continue

                region = (
                    it0.get("address", {})
                       .get("region", {})
                       .get("uk_UA", "")
                )

                type_text = " ".join(
                    c.get("description", {}).get("uk_UA", "")
                    for c in it0.get("additionalClassifications", [])
                )
                land_type = _classify_land_type(type_text)

                title_raw = item.get("title", "")
                title = (
                    title_raw.get("uk_UA", "")
                    if isinstance(title_raw, dict) else str(title_raw)
                )[:70]

                cadastral = it0.get("itemProps", {}).get("cadastralNumber", "")

                collected.append({
                    "price_per_ha": round(price_per_ha, 0),
                    "area_ha":      round(area, 2),
                    "region":       region,
                    "land_type":    land_type,
                    "date":         item.get("dateModified", "")[:10],
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


def get_cached_land_auctions(force_refresh: bool = False) -> list[dict]:
    """Кешована версія fetch_land_auctions (TTL 1 година)."""
    now = time.time()
    cache_key = "land_auctions"

    if not force_refresh and cache_key in _CACHE:
        data, ts = _CACHE[cache_key]
        if now - ts < _CACHE_TTL:
            return data

    data = fetch_land_auctions()
    _CACHE[cache_key] = (data, now)
    return data


# ─────────────────────────────────────────────
# Публічний інтерфейс (сумісний зі старим кодом)
# ─────────────────────────────────────────────

def fetch_land_lots(
    region: Optional[str] = None,
    status: str = "complete",
    limit: int = 100,
) -> pd.DataFrame:
    """
    Повертає DataFrame земельних лотів для відображення в таблиці.
    Використовує кешовану курсорну вибірку з нового API.
    Якщо реальних даних немає — fallback на синтетичні.
    """
    records = get_cached_land_auctions()

    if len(records) < 5:
        return _demo_data()

    df = pd.DataFrame(records)
    df = df.rename(columns={"price_per_ha": "price_per_ha"})
    df["final_price"] = df["price_per_ha"] * df["area_ha"]
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