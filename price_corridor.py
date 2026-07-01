"""
TerraAudit — Ціновий коридор
Реальні дані з Прозорро.Продажі + фолбек на базові орієнтири.
"""

import requests
import numpy as np
import time
from typing import Optional

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
# ПРОЗОРРО.ПРОДАЖІ: реальні ціни аукціонів
# ─────────────────────────────────────────────

# Тип землі → CAV-коди Прозорро
_LAND_TYPE_TO_CAV = {
    "Сільське господарство": "04110000-4",
    "Пасовище":              "04110000-4",   # теж с/г категорія
    "Забудова":              "04200000-1",
    "Промисловість":         "04300000-8",
}

def fetch_prozorro_prices(
    land_type: str,
    area_ha: float,
    limit: int = 50,
) -> list[float]:
    """
    Тягне ціни завершених аукціонів з Прозорро.Продажі.
    Повертає список грн/га/рік для побудови коридору.

    Якщо API недоступний або повернув < 5 записів — фолбек на базові орієнтири.
    """
    cav = _LAND_TYPE_TO_CAV.get(land_type, "04000000-8")
    prices_per_ha = []

    try:
        r = requests.get(
            "https://prozorro.sale/api/auctions",
            params={
                "limit": limit,
                "status": "complete",
                "classification.id": cav,
            },
            timeout=8,
        )

        if r.status_code == 200:
            for item in r.json().get("data", []):
                try:
                    lots = item.get("lots", [{}])
                    area = float(lots[0].get("quantity", 0)) if lots else 0.0
                    awards = item.get("awards", [])
                    if not awards or area <= 0:
                        continue

                    final_price = float(
                        awards[-1].get("value", {}).get("amount", 0)
                    )
                    if final_price <= 0:
                        continue

                    ppha = final_price / area
                    # Санітарна перевірка: ціна в розумному діапазоні
                    if 500 < ppha < 500_000:
                        prices_per_ha.append(ppha)

                except (KeyError, ValueError, TypeError, ZeroDivisionError):
                    continue

    except Exception as e:
        print(f"⚠️ Прозорро API недоступний: {e}")

    # Якщо реальних даних замало — беремо базові орієнтири
    if len(prices_per_ha) < 5:
        prices_per_ha = _fallback_prices(land_type)

    return prices_per_ha


def _fallback_prices(land_type: str) -> list[float]:
    """
    Базові орієнтири вартості оренди землі (грн/га/рік).
    Наближені до реальних даних аукціонів 2023-2024.
    """
    usd = get_real_exchange_rate()

    # Базові USD/га/рік за типом, наближені до ринку
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
    input_price: Optional[float] = None,
) -> tuple:
    """
    Обчислює ціновий коридор для ділянки.

    Args:
        area_hectares: площа ділянки
        land_type: тип за кадастром
        input_price: ціна для перевірки (з повзунка демо)

    Returns:
        (min_total, max_total, median_total) — загальна ціна оренди грн/рік
    """
    if area_hectares <= 0:
        return 0, 0, 0

    prices = fetch_prozorro_prices(land_type, area_hectares)

    p25    = float(np.percentile(prices, 25))
    median = float(np.median(prices))
    p85    = float(np.percentile(prices, 85))

    return (
        int(p25    * area_hectares),
        int(p85    * area_hectares),
        int(median * area_hectares),
    )


def price_verdict(
    proposed: float,
    min_price: float,
    max_price: float,
    median_price: float,
) -> dict:
    """
    Вердикт для демо-повзунка на пітчі.

    Returns:
        {"verdict": "fair"|"suspicious_low"|"suspicious_high",
         "deviation_pct": float,
         "message": str}
    """
    if median_price <= 0:
        return {"verdict": "unknown", "deviation_pct": 0, "message": "Недостатньо даних"}

    dev = round((proposed - median_price) / median_price * 100, 1)

    if proposed < min_price:
        return {
            "verdict": "suspicious_low",
            "deviation_pct": dev,
            "message": (
                f"⛔ Ціна нижча за 25-й перцентиль ринку ({min_price:,.0f} грн). "
                f"Відхилення: {dev:+.1f}%. Ризик тіньової угоди."
            ),
        }
    elif proposed > max_price * 1.3:
        return {
            "verdict": "suspicious_high",
            "deviation_pct": dev,
            "message": (
                f"⚠️ Ціна підозріло висока (>{max_price:,.0f} грн). "
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