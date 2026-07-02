"""
TerraAudit — GeoAI Engine
Sentinel-2 NDVI time-series + VIIRS нічні вогні + Sentinel-1 SAR
Має повноцінний demo-режим якщо GEE не підключений.
"""

import ee
import requests
import numpy as np
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
# Ініціалізація GEE
# ─────────────────────────────────────────────

EE_IS_ACTIVE = False

def init_gee(project: str = None):
    """
    Ініціалізація Google Earth Engine.
    Підтримує три середовища автоматично:
      1. Локально — після python auth.py
      2. Streamlit Cloud — GEE_CREDENTIALS з Secrets
      3. Demo-режим — якщо GEE недоступний
    """
    global EE_IS_ACTIVE
    import os, json
    project = project or os.environ.get("GEE_PROJECT", "terraaudit-hackathon")

    # Streamlit Cloud: записуємо credentials з Secrets у стандартний шлях
    gee_creds = os.environ.get("GEE_CREDENTIALS")
    if gee_creds:
        try:
            creds_path = os.path.expanduser("~/.config/earthengine/credentials")
            os.makedirs(os.path.dirname(creds_path), exist_ok=True)
            with open(creds_path, "w") as f:
                f.write(gee_creds)
        except Exception as e:
            print(f"⚠️ Не вдалось записати GEE credentials: {e}")

    try:
        ee.Initialize(project=project)
        EE_IS_ACTIVE = True
    except Exception:
        try:
            ee.Authenticate()
            ee.Initialize(project=project)
            EE_IS_ACTIVE = True
        except Exception as e:
            print(f"⚠️ GEE недоступний, використовується demo-режим: {e}")
            EE_IS_ACTIVE = False

# Намагаємось ініціалізувати при імпорті
init_gee()


# ─────────────────────────────────────────────
# Геокодування
# ─────────────────────────────────────────────

def get_coordinates_by_address(address: str):
    """Шукає координати за текстом через Nominatim (OpenStreetMap)."""
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": "TerraAudit_Hackathon_App/1.0"}
    params = {"q": address, "format": "json", "limit": 1}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        if r.status_code == 200 and r.json():
            d = r.json()[0]
            return float(d["lat"]), float(d["lon"]), d["display_name"]
    except Exception:
        pass
    return None, None, None


# ─────────────────────────────────────────────
# ДОПОМІЖНІ ФУНКЦІЇ GEE
# ─────────────────────────────────────────────

def _mask_s2_clouds(image):
    """Маскування хмар через QA60."""
    qa = image.select("QA60")
    mask = (
        qa.bitwiseAnd(1 << 10).eq(0)
        .And(qa.bitwiseAnd(1 << 11).eq(0))
    )
    return image.updateMask(mask).divide(10000)


def _add_ndvi(image):
    return image.addBands(
        image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    )


def _add_ndbi(image):
    return image.addBands(
        image.normalizedDifference(["B11", "B8"]).rename("NDBI")
    )


# ─────────────────────────────────────────────
# NDVI ЧАСОВИЙ РЯД (головний модуль)
# ─────────────────────────────────────────────

def get_ndvi_timeseries(
    lat: float,
    lon: float,
    start_year: int = 2021,
    end_year: int = None,
    buffer_m: int = 300,
) -> pd.DataFrame:
    """
    Будує місячний NDVI + NDBI часовий ряд через GEE.
    Якщо GEE недоступний — повертає demo-дані.
    """
    if end_year is None:
        end_year = datetime.now().year - 1  # поточний рік неповний
    if not EE_IS_ACTIVE:
        return _demo_ndvi_timeseries(start_year, end_year)

    try:
        aoi = ee.Geometry.Point([lon, lat]).buffer(buffer_m)
        col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(aoi)
            .filterDate(f"{start_year}-01-01", f"{end_year}-12-31")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
            .map(_mask_s2_clouds)
            .map(_add_ndvi)
            .map(_add_ndbi)
        )

        def extract(img):
            date = img.date().format("YYYY-MM-dd")
            stats = img.select(["NDVI", "NDBI"]).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=10,
                maxPixels=1e9,
            )
            return ee.Feature(None, {
                "date": date,
                "NDVI": stats.get("NDVI"),
                "NDBI": stats.get("NDBI"),
            })

        rows = col.map(extract).getInfo()["features"]
        records = [
            f["properties"] for f in rows
            if f["properties"].get("NDVI") is not None
        ]

        if not records:
            return _demo_ndvi_timeseries(start_year, end_year)

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        df["source"] = "GEE (Sentinel-2)"
        return df

    except Exception as e:
        print(f"⚠️ GEE NDVI помилка: {e}")
        return _demo_ndvi_timeseries(start_year, end_year)


# ─────────────────────────────────────────────
# VIIRS НІЧНІ ВОГНІ
# ─────────────────────────────────────────────

def get_viirs_nightlights(
    lat: float,
    lon: float,
    start_year: int = 2021,
    end_year: int = None,
    buffer_m: int = 500,
) -> pd.DataFrame:
    """Місячний ряд нічної яскравості VIIRS для ділянки."""
    if end_year is None:
        end_year = datetime.now().year - 1  # поточний рік неповний
    if not EE_IS_ACTIVE:
        return _demo_viirs(start_year, end_year)

    try:
        aoi = ee.Geometry.Point([lon, lat]).buffer(buffer_m)
        col = (
            ee.ImageCollection("NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG")
            .filterBounds(aoi)
            .filterDate(f"{start_year}-01-01", f"{end_year}-12-31")
            .select("avg_rad")
        )

        def extract(img):
            stats = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=500,
                maxPixels=1e9,
            )
            return ee.Feature(None, {
                "date": img.date().format("YYYY-MM"),
                "avg_radiance": stats.get("avg_rad"),
            })

        rows = col.map(extract).getInfo()["features"]
        records = [
            f["properties"] for f in rows
            if f["properties"].get("avg_radiance") is not None
        ]

        if not records:
            return _demo_viirs(start_year, end_year)

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        df["source"] = "GEE (VIIRS)"
        return df.sort_values("date").reset_index(drop=True)

    except Exception as e:
        print(f"⚠️ GEE VIIRS помилка: {e}")
        return _demo_viirs(start_year, end_year)


# ─────────────────────────────────────────────
# SENTINEL-1 SAR (реальний)
# ─────────────────────────────────────────────

def get_sar_change(
    lat: float,
    lon: float,
    baseline: tuple = ("2021-01-01", "2021-12-31"),
    current:  tuple = ("2023-01-01", "2023-12-31"),
    buffer_m: int = 300,
) -> dict:
    """
    Порівнює SAR backscatter (VV) між двома періодами.
    Зміна > 3 dB = земляні роботи / нова будівля / розчищення.
    """
    if not EE_IS_ACTIVE:
        return _demo_sar()

    try:
        aoi = ee.Geometry.Point([lon, lat]).buffer(buffer_m)

        def mean_vv(start, end):
            col = (
                ee.ImageCollection("COPERNICUS/S1_GRD")
                .filterBounds(aoi)
                .filterDate(start, end)
                .filter(ee.Filter.eq("instrumentMode", "IW"))
                .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
                .select("VV")
                .mean()
            )
            val = col.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=aoi,
                scale=10,
                maxPixels=1e9,
            ).get("VV").getInfo()
            return val if val is not None else -15.0

        b = mean_vv(*baseline)
        c = mean_vv(*current)
        delta = c - b

        return {
            "baseline_db": round(b, 2),
            "current_db":  round(c, 2),
            "delta_db":    round(delta, 2),
            "changed":     abs(delta) > 3.0,
            "source":      "GEE (Sentinel-1 SAR)",
        }
    except Exception as e:
        print(f"⚠️ GEE SAR помилка: {e}")
        return _demo_sar()


# ─────────────────────────────────────────────
# ГОЛОВНА ФУНКЦІЯ АНАЛІЗУ (для app.py)
# ─────────────────────────────────────────────

def analyze_satellite_data(lat: float, lon: float, year: int = 2023) -> dict:
    """
    Повний аналіз ділянки: NDVI snapshot + VIIRS + SAR.
    year — рік для якого робиться snapshot (впливає на значення NDVI/VIIRS).
    Завжди повертає результат (real або demo).
    """
    # NDVI — snapshot за обраний рік (літні місяці для максимального NDVI)
    ndvi_df = get_ndvi_timeseries(lat, lon, start_year=year, end_year=year)
    ndvi_val = float(ndvi_df["NDVI"].mean()) if len(ndvi_df) > 0 else 0.15
    ndbi_val = float(ndvi_df["NDBI"].mean()) if "NDBI" in ndvi_df.columns else 0.0

    # VIIRS — середня за обраний рік
    viirs_df = get_viirs_nightlights(lat, lon, start_year=year, end_year=year)
    viirs_val = float(viirs_df["avg_radiance"].mean()) if len(viirs_df) > 0 else 0.0

    # SAR — порівнює рік до обраного vs обраний рік
    baseline_year = max(year - 1, 2020)
    sar = get_sar_change(
        lat, lon,
        baseline=(f"{baseline_year}-01-01", f"{baseline_year}-12-31"),
        current=(f"{year}-01-01",           f"{year}-12-31"),
    )

    source_label = f"GEE (реальні дані, {year}р.)" if EE_IS_ACTIVE else "Demo-режим (GEE не підключено)"

    return {
        "status":               "success",
        "ndvi_score":           round(ndvi_val, 3),
        "ndbi_score":           round(ndbi_val, 3),
        "night_light_rad":      round(viirs_val, 2),
        "sar_detected_changes": sar["changed"],
        "sar_delta_db":         sar["delta_db"],
        "source":               source_label,
        "is_demo":              not EE_IS_ACTIVE,
        "year":                 year,
    }


# ─────────────────────────────────────────────
# DEMO FALLBACK ГЕНЕРАТОРИ
# ─────────────────────────────────────────────

def _demo_ndvi_timeseries(start_year: int, end_year: int) -> pd.DataFrame:
    """
    Синтетичний NDVI для демо.
    Симулює закинуту с/г ділянку з низькою сезонністю + підозрілим NDBI.
    """
    np.random.seed(42)
    dates = pd.date_range(f"{start_year}-01-01", f"{end_year}-12-01", freq="MS")
    t = np.arange(len(dates))

    # Покидані землі: низький плаский NDVI без чіткого сезонного циклу
    ndvi = (
        0.18
        + 0.06 * np.sin(2 * np.pi * t / 12)   # слабка сезонність
        + np.random.normal(0, 0.015, len(t))
    ).clip(0.05, 0.40)

    # NDBI злегка позитивний → ознаки твердого покриття
    ndbi = np.random.uniform(0.03, 0.18, len(t))

    return pd.DataFrame({
        "date":   dates,
        "NDVI":   ndvi,
        "NDBI":   ndbi,
        "source": "Demo (GEE не підключено)",
    })


def _demo_viirs(start_year: int, end_year: int) -> pd.DataFrame:
    """Синтетична нічна активність — підозріло висока для 'пустиря'."""
    np.random.seed(7)
    dates = pd.date_range(f"{start_year}-01-01", f"{end_year}-12-01", freq="MS")
    radiance = np.random.uniform(2.8, 6.5, len(dates))
    return pd.DataFrame({
        "date":         dates,
        "avg_radiance": radiance,
        "source":       "Demo (GEE не підключено)",
    })


def _demo_sar() -> dict:
    """Синтетичні SAR-дані — фіксована зміна поверхні."""
    return {
        "baseline_db": -14.5,
        "current_db":  -10.8,
        "delta_db":     3.7,
        "changed":      True,
        "source":       "Demo (GEE не підключено)",
    }