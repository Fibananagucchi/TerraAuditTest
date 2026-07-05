"""
TerraAudit — Ціновий коридор (v2)
Реальні дані з нового Prozorro API (курсорна пагінація) + фолбек.
Фільтрація по регіону та схожій площі.
"""

import requests
import numpy as np
import re
from typing import Optional

import prozorro  # новий модуль з fetch_land_auctions

# ─────────────────────────────────────────────
# НБУ: Поточний курс USD
# ─────────────────────────────────────────────

def get_real_exchange_rate() -> float:
    """Офіційний курс USD/UAH з API Нацбанку."""
    try:
        r = requests.get(
            "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
            "?valcode=USD&json",
            timeout=5,
        )
        if r.status_code == 200:
            return float(r.json()[0]["rate"])
    except Exception:
        pass
    return 41.0  # фолбек


# ─────────────────────────────────────────────
# Визначення регіону з адреси
# ─────────────────────────────────────────────

UKRAINE_REGIONS = [
    "Черкаська", "Полтавська", "Вінницька", "Київська", "Харківська",
    "Львівська", "Одеська", "Дніпропетровська", "Запорізька", "Донецька",
    "Луганська", "Сумська", "Житомирська", "Хмельницька", "Тернопільська",
    "Івано-Франківська", "Чернівецька", "Волинська", "Рівненська",
    "Закарпатська", "Миколаївська", "Херсонська", "Кіровоградська",
    "Чернігівська",
]


def extract_region(address: str) -> Optional[str]:
    """Витягує назву області з рядка адреси."""
    if not address:
        return None
    for region in UKRAINE_REGIONS:
        if region.lower() in address.lower():
            return region
    return None


# ─────────────────────────────────────────────
# ПРОЗОРРО: реальні ціни через новий API
# ─────────────────────────────────────────────

def fetch_prozorro_prices(
    land_type: str,
    area_ha: float,
    region: Optional[str] = None,
    start_year: Optional[int] = None,
) -> tuple:
    """
    Тягне ціни завершених земельних аукціонів з нового Prozorro API.
    4-рівнева фільтрація: регіон+площа → регіон → тип по країні → fallback.
    start_year — з якого року шукати (прив'язка до "Аналіз від" в UI).

    Returns:
        (prices_per_ha: list[float], match_level: str)
    """
    try:
        all_records = prozorro.get_cached_land_auctions(start_year=start_year)
    except Exception as e:
        print(f"⚠️ Прозорро недоступний: {e}")
        all_records = []

    if not all_records:
        return _fallback_prices(land_type), "fallback"

    # Фільтруємо по типу землі
    type_matched = [r for r in all_records if r.get("land_type") == land_type]

    # ── Рівень 1: регіон + схожа площа (±50%) ──
    if region and type_matched:
        regional_similar = [
            r["price_per_ha"] for r in type_matched
            if region.lower() in r.get("region", "").lower()
            and area_ha * 0.5 <= r["area_ha"] <= area_ha * 1.5
        ]
        if len(regional_similar) >= 5:
            return regional_similar, "regional"

    # ── Рівень 2: тільки регіон ──
    if region and type_matched:
        regional_only = [
            r["price_per_ha"] for r in type_matched
            if region.lower() in r.get("region", "").lower()
        ]
        if len(regional_only) >= 5:
            return regional_only, "regional"

    # ── Рівень 3: вся країна, цей тип землі ──
    national = [r["price_per_ha"] for r in type_matched]
    if len(national) >= 5:
        return national, "national"

    # ── Рівень 3.5: вся країна, будь-який тип (якщо типу замало) ──
    any_type = [r["price_per_ha"] for r in all_records]
    if len(any_type) >= 5:
        return any_type, "national"

    # ── Рівень 4: fallback ──
    return _fallback_prices(land_type), "fallback"


def _fallback_prices(land_type: str) -> list:
    """Базові орієнтири вартості оренди землі (грн/га/рік)."""
    usd = get_real_exchange_rate()
    base_usd = {
        "Сільське господарство": [280, 320, 360, 400, 450, 380, 310, 420],
        "Пасовище":              [150, 180, 200, 220, 170, 190, 210, 165],
        "Забудова":              [2800, 3500, 4200, 5000, 3200, 4800, 3900, 4500],
        "Промисловість":         [1000, 1300, 1600, 1900, 1200, 1500, 1100, 1800],
    }.get(land_type, [1000, 1200, 1400, 1100, 1300])
    return [p * usd for p in base_usd]


# ─────────────────────────────────────────────
# ГОЛОВНА ФУНКЦІЯ: Ціновий коридор
# ─────────────────────────────────────────────

def calculate_corridor(
    area_hectares: float,
    land_type: str,
    address: Optional[str] = None,
    input_price: Optional[float] = None,
    start_year: Optional[int] = None,
) -> tuple:
    """
    Обчислює ціновий коридор для ділянки з урахуванням регіону.
    start_year — рік з якого шукати порівняльні лоти (з "Аналіз від" в UI).

    Returns:
        (min_total, max_total, median_total, match_level)
    """
    if area_hectares <= 0:
        return 0, 0, 0, "none"

    region = extract_region(address) if address else None
    prices, match_level = fetch_prozorro_prices(land_type, area_hectares, region, start_year)

    p25    = float(np.percentile(prices, 25))
    median = float(np.median(prices))
    p85    = float(np.percentile(prices, 85))

    return (
        int(p25    * area_hectares),
        int(p85    * area_hectares),
        int(median * area_hectares),
        match_level,
    )


def price_verdict(
    proposed: float,
    min_price: float,
    max_price: float,
    median_price: float,
) -> dict:
    """
    Вердикт для демо-повзунка на пітчі.

    Перевіряє ДВІ умови незалежно:
    1. Абсолютний поріг — чи нижче P25 / вище P85*1.3
    2. Відносне відхилення від медіани (%) — навіть якщо P25 сам по собі
       низький через широкий розкид вибірки, велике відхилення від
       медіани (>50%) все одно має позначатись як підозріле.
    """
    if median_price <= 0:
        return {"verdict": "unknown", "deviation_pct": 0, "message": "Недостатньо даних"}

    dev = round((proposed - median_price) / median_price * 100, 1)

    is_below_p25   = proposed < min_price
    is_way_below   = dev <= -50.0   # більше half медіани вниз — підозріло незалежно від P25
    is_above_p85   = proposed > max_price * 1.3
    is_way_above   = dev >= 100.0   # вдвічі вище медіани і більше

    if is_below_p25 or is_way_below:
        reason = (
            f"нижча за 25-й перцентиль ринку ({min_price:,.0f} грн)"
            if is_below_p25 else
            f"на {abs(dev):.0f}% нижча за медіану"
        )
        return {
            "verdict": "suspicious_low",
            "deviation_pct": dev,
            "message": (
                f"⛔ Ціна {reason}. "
                f"Відхилення: {dev:+.1f}%. Ризик тіньової угоди."
            ),
        }
    elif is_above_p85 or is_way_above:
        reason = (
            f"вища за розумний максимум ({max_price:,.0f} грн)"
            if is_above_p85 else
            f"на {dev:.0f}% вища за медіану"
        )
        return {
            "verdict": "suspicious_high",
            "deviation_pct": dev,
            "message": (
                f"⚠️ Ціна {reason}. "
                f"Відхилення: {dev:+.1f}%. Можливе завищення."
            ),
        }
    else:
        return {
            "verdict": "fair",
            "deviation_pct": dev,
            "message": (
                f"✅ Ціна у справедливому ринковому діапазоні. "
                f"Відхилення від медіани: {dev:+.1f}%."
            ),
        }