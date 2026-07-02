"""
TerraAudit — Модуль аналізу
Asset Score, таблиця порівняння кадастр vs супутник.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass


# ─────────────────────────────────────────────
# Asset Score
# ─────────────────────────────────────────────

@dataclass
class AssetScore:
    score: float          # 0..10
    label: str            # "Низький" | "Середній" | "Високий" | "Критичний"
    color: str            # hex для UI
    emoji: str
    summary: str          # одне речення для журі
    breakdown: dict       # {компонент: бал} для деталей


def calculate_asset_score(
    ndvi: float,
    ndbi: float,
    viirs: float,
    sar_changed: bool,
    land_type: str,
    area_ha: float,
) -> AssetScore:
    """
    Єдиний скоринг потенціалу монетизації ділянки (0-10).

    Логіка:
    - Низький NDVI на с/г землі = актив не використовується (+)
    - Позитивний NDBI = тверде покриття / забудова (+)
    - Висока нічна активність на "пустирі" = прихована діяльність (+)
    - SAR зміна = щось відбувається (+)
    - Більша площа = більший потенційний дохід (+)
    """
    breakdown = {}
    total = 0.0

    # 1. NDVI компонент (0-3 балів)
    is_agri = land_type in ("Сільське господарство", "Пасовище")
    if is_agri and ndvi < 0.15:
        ndvi_score = 3.0
        ndvi_label = "Критично низький для с/г"
    elif is_agri and ndvi < 0.25:
        ndvi_score = 2.0
        ndvi_label = "Нижче норми для с/г"
    elif is_agri and ndvi < 0.35:
        ndvi_score = 1.0
        ndvi_label = "Погранична норма"
    else:
        ndvi_score = 0.0
        ndvi_label = "Норма"
    breakdown["NDVI (рослинність)"] = (ndvi_score, f"{ndvi:.3f} — {ndvi_label}")
    total += ndvi_score

    # 2. NDBI компонент (0-2 балів)
    if ndbi > 0.15:
        ndbi_score = 2.0
        ndbi_label = "Значне тверде покриття"
    elif ndbi > 0.05:
        ndbi_score = 1.0
        ndbi_label = "Ознаки твердого покриття"
    else:
        ndbi_score = 0.0
        ndbi_label = "Природна поверхня"
    breakdown["NDBI (забудованість)"] = (ndbi_score, f"{ndbi:.3f} — {ndbi_label}")
    total += ndbi_score

    # 3. VIIRS компонент (0-3 балів)
    if viirs > 4.0:
        viirs_score = 3.0
        viirs_label = "Висока нічна активність"
    elif viirs > 2.0:
        viirs_score = 2.0
        viirs_label = "Помірна нічна активність"
    elif viirs > 1.0:
        viirs_score = 1.0
        viirs_label = "Слабка нічна активність"
    else:
        viirs_score = 0.0
        viirs_label = "Нічної активності немає"
    breakdown["VIIRS (нічна активність)"] = (viirs_score, f"{viirs:.2f} нВт — {viirs_label}")
    total += viirs_score

    # 4. SAR компонент (0-1 балів)
    sar_score = 1.0 if sar_changed else 0.0
    sar_label = "Зміну поверхні виявлено" if sar_changed else "Поверхня стабільна"
    breakdown["SAR (зміна поверхні)"] = (sar_score, sar_label)
    total += sar_score

    # 5. Площа бонус (0-1 балів)
    area_score = min(area_ha / 20.0, 1.0)
    breakdown["Площа активу"] = (round(area_score, 1), f"{area_ha} га")
    total += area_score

    total = min(round(total, 1), 10.0)

    # Визначаємо рівень
    if total >= 7.0:
        label, color, emoji = "Критичний", "#e74c3c", "🔴"
        summary = "Ділянка має ознаки нецільового використання — пріоритет для аудиту"
    elif total >= 5.0:
        label, color, emoji = "Високий", "#e67e22", "🟠"
        summary = "Значний нереалізований потенціал — рекомендується виставити на Прозорро"
    elif total >= 3.0:
        label, color, emoji = "Середній", "#f1c40f", "🟡"
        summary = "Помірний потенціал монетизації — потребує додаткової перевірки"
    else:
        label, color, emoji = "Низький", "#27ae60", "🟢"
        summary = "Ділянка використовується за призначенням — аномалій не виявлено"

    return AssetScore(
        score=total,
        label=label,
        color=color,
        emoji=emoji,
        summary=summary,
        breakdown=breakdown,
    )


# ─────────────────────────────────────────────
# Таблиця порівняння: Кадастр vs Супутник
# ─────────────────────────────────────────────

def build_comparison_table(
    land_type: str,
    ndvi: float,
    ndbi: float,
    viirs: float,
    sar_changed: bool,
) -> pd.DataFrame:
    """
    Будує таблицю "офіційний статус vs реальність за супутником".
    """
    is_agri = land_type in ("Сільське господарство", "Пасовище")

    rows = []

    # Землекористування
    official_use = land_type
    if ndbi > 0.1:
        sat_use = "Забудова / тверде покриття"
        status = "🚨 Розбіжність"
    elif ndvi < 0.2 and is_agri:
        sat_use = "Незадіяна / закинута"
        status = "⚠️ Не відповідає"
    else:
        sat_use = land_type
        status = "✅ Відповідає"
    rows.append(["Землекористування", official_use, sat_use, status])

    # Рослинність
    if is_agri:
        official_veg = "Очікується (NDVI > 0.35)"
        sat_veg = f"NDVI = {ndvi:.3f}"
        veg_status = "✅ Норма" if ndvi >= 0.35 else ("⚠️ Низька" if ndvi >= 0.2 else "🚨 Критично низька")
        rows.append(["Рослинність (NDVI)", official_veg, sat_veg, veg_status])

    # Нічна активність
    rows.append([
        "Нічна активність",
        "Не очікується (житлова/с-г)",
        f"VIIRS = {viirs:.2f} нВт",
        "🚨 Виявлено" if viirs > 2.0 else "✅ Відсутня",
    ])

    # Зміна поверхні
    rows.append([
        "Зміна поверхні (SAR)",
        "Не очікується",
        "Виявлено (Δ > 3 dB)" if sar_changed else "Не виявлено",
        "⚠️ Зміна" if sar_changed else "✅ Стабільна",
    ])

    return pd.DataFrame(rows, columns=["Параметр", "📋 Кадастр", "🛰️ Супутник", "Статус"])


# ─────────────────────────────────────────────
# Demo кейс (pre-loaded)
# ─────────────────────────────────────────────

DEMO_CASES = {
    "🚨 Закинута с/г земля (Черкаська обл.)": {
        "lat": 49.444,
        "lon": 31.998,
        "area_ha": 8.5,
        "land_type": "Сільське господарство",
        "address": "Черкаська обл., Смілянський р-н",
        "sat_data": {
            "ndvi_score": 0.12,
            "ndbi_score": 0.18,
            "night_light_rad": 4.2,
            "sar_detected_changes": True,
            "sar_delta_db": 4.1,
            "source": "Demo кейс (pre-loaded)",
            "is_demo": True,
            "status": "success",
        },
    },
    "🟡 Пасовище з помірним потенціалом (Полтавська обл.)": {
        "lat": 49.588,
        "lon": 34.551,
        "area_ha": 12.0,
        "land_type": "Пасовище",
        "address": "Полтавська обл., Кременчуцький р-н",
        "sat_data": {
            "ndvi_score": 0.22,
            "ndbi_score": 0.04,
            "night_light_rad": 1.8,
            "sar_detected_changes": False,
            "sar_delta_db": 1.2,
            "source": "Demo кейс (pre-loaded)",
            "is_demo": True,
            "status": "success",
        },
    },
    "✅ Активна ферма (Вінницька обл.)": {
        "lat": 49.233,
        "lon": 28.468,
        "area_ha": 25.0,
        "land_type": "Сільське господарство",
        "address": "Вінницька обл., Вінницький р-н",
        "sat_data": {
            "ndvi_score": 0.61,
            "ndbi_score": -0.12,
            "night_light_rad": 0.3,
            "sar_detected_changes": False,
            "sar_delta_db": 0.8,
            "source": "Demo кейс (pre-loaded)",
            "is_demo": True,
            "status": "success",
        },
    },
}