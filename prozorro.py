"""
TerraAudit — Прозорро.Продажі API клієнт
Отримання реальних даних земельних аукціонів.
"""

import requests
import pandas as pd
import numpy as np
import time
from typing import Optional


PROZORRO_API = "https://prozorro.sale/api"


def fetch_land_lots(
    region: Optional[str] = None,
    status: str = "complete",
    limit: int = 100,
) -> pd.DataFrame:
    """
    Отримує список земельних лотів з API Прозорро.Продажі.
    Якщо API недоступний — повертає демо-дані.
    """
    records = []

    try:
        params = {
            "limit": min(limit, 50),
            "status": status,
            "classification.id": "04000000-8",
        }

        r = requests.get(
            f"{PROZORRO_API}/auctions",
            params=params,
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
                    if not (500 < ppha < 500_000):
                        continue

                    records.append({
                        "id":           item.get("id", ""),
                        "title":        item.get("title", "Земельна ділянка")[:60],
                        "area_ha":      round(area, 2),
                        "final_price":  round(final_price, 0),
                        "price_per_ha": round(ppha, 0),
                        "region":       item.get("procuringEntity", {})
                                           .get("address", {})
                                           .get("region", ""),
                        "date":         item.get("dateModified", "")[:10],
                    })
                except (KeyError, ValueError, TypeError, ZeroDivisionError):
                    continue

    except Exception as e:
        print(f"⚠️ Прозорро API: {e}")

    if len(records) < 5:
        return _demo_data()

    return pd.DataFrame(records)


def _demo_data() -> pd.DataFrame:
    """Демо-дані коли API недоступний."""
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
            "date":         f"2023-{np.random.randint(1,13):02d}-{np.random.randint(1,28):02d}",
        })
    return pd.DataFrame(records)


def get_comparable_prices(
    df: pd.DataFrame,
    region: str,
    area_ha: float,
    tolerance: float = 0.5,
) -> list:
    """Фільтрує порівняльні ціни для побудови цінового коридору."""
    filtered = df[
        (df["region"].str.contains(region, case=False, na=False)) &
        (df["price_per_ha"] > 0) &
        (df["area_ha"].between(area_ha * (1 - tolerance), area_ha * (1 + tolerance)))
    ]
    if len(filtered) < 5:
        filtered = df[
            (df["region"].str.contains(region, case=False, na=False)) &
            (df["price_per_ha"] > 0)
        ]
    return filtered["price_per_ha"].tolist()