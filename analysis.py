"""
TerraAudit — Модуль аналізу
Asset Score, таблиця порівняння кадастр vs супутник.

Логіка по типу землі:
  Сільське господарство / Пасовище:
    - Низький NDVI = не обробляється (аномалія)
    - Високий NDBI = тверде покриття на с/г землі (аномалія)
    - Висока VIIRS = прихована нічна діяльність (аномалія)
    - SAR зміна = будівництво на с/г землі (аномалія)

  Забудова / Промисловість:
    - Низький NDVI = норма (немає рослинності)
    - Високий NDBI = норма (є будівлі)
    - Висока VIIRS = норма (є освітлення, активність)
    - SAR зміна = норма (будівництво/ремонт)
    - Аномалія тут: низька активність при задекларованій забудові
      (ділянка може бути занедбаною)
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass


# ─────────────────────────────────────────────
# Asset Score
# ─────────────────────────────────────────────

@dataclass
class AssetScore:
    score: float
    label: str
    color: str
    emoji: str
    summary: str
    breakdown: dict


def calculate_asset_score(
    ndvi: float,
    ndbi: float,
    viirs: float,
    sar_changed: bool,
    land_type: str,
    area_ha: float,
) -> AssetScore:

    breakdown = {}
    total = 0.0

    is_agri    = land_type in ("Сільське господарство", "Пасовище")
    is_built   = land_type in ("Забудова", "Промисловість")

    # ── 1. NDVI (0–3 балів) ───────────────────────────────────────────────
    if is_agri:
        # С/г: низький NDVI = не обробляється = потенціал
        if ndvi < 0.15:
            ndvi_score, ndvi_label = 3.0, "Критично низький для с/г"
        elif ndvi < 0.25:
            ndvi_score, ndvi_label = 2.0, "Нижче норми для с/г"
        elif ndvi < 0.35:
            ndvi_score, ndvi_label = 1.0, "Погранична норма"
        else:
            ndvi_score, ndvi_label = 0.0, "Норма"
    elif is_built:
        # Забудова: зелень = можлива занедбаність (слабкий сигнал)
        if ndvi > 0.4:
            ndvi_score, ndvi_label = 1.0, "Заростає рослинністю — можлива занедбаність"
        else:
            ndvi_score, ndvi_label = 0.0, "Норма для забудови"
    else:
        ndvi_score, ndvi_label = 0.0, "Норма"

    breakdown["NDVI (рослинність)"] = (ndvi_score, f"{ndvi:.3f} — {ndvi_label}")
    total += ndvi_score

    # ── 2. NDBI (0–2 балів) ───────────────────────────────────────────────
    if is_agri:
        # С/г: тверде покриття там де має бути поле = аномалія
        if ndbi > 0.15:
            ndbi_score, ndbi_label = 2.0, "Тверде покриття на с/г землі"
        elif ndbi > 0.05:
            ndbi_score, ndbi_label = 1.0, "Ознаки твердого покриття"
        else:
            ndbi_score, ndbi_label = 0.0, "Природна поверхня"
    elif is_built:
        # Забудова: відсутність твердого покриття = можлива занедбаність
        if ndbi < 0.0:
            ndbi_score, ndbi_label = 1.5, "Низький NDBI — ділянка може бути незабудована"
        elif ndbi < 0.05:
            ndbi_score, ndbi_label = 0.5, "Слабке тверде покриття для забудови"
        else:
            ndbi_score, ndbi_label = 0.0, "Норма для забудови"
    else:
        ndbi_score, ndbi_label = 0.0, "Норма"

    breakdown["NDBI (забудованість)"] = (ndbi_score, f"{ndbi:.3f} — {ndbi_label}")
    total += ndbi_score

    # ── 3. VIIRS (0–3 балів) ──────────────────────────────────────────────
    if is_agri:
        # С/г: нічна активність на полі = прихована діяльність
        if viirs > 4.0:
            viirs_score, viirs_label = 3.0, "Висока нічна активність на с/г ділянці"
        elif viirs > 2.0:
            viirs_score, viirs_label = 2.0, "Помірна нічна активність"
        elif viirs > 1.0:
            viirs_score, viirs_label = 1.0, "Слабка нічна активність"
        else:
            viirs_score, viirs_label = 0.0, "Нічної активності немає — норма"
    elif is_built:
        # Забудова: відсутність нічних вогнів = занедбана
        if viirs < 0.5:
            viirs_score, viirs_label = 2.0, "Немає нічної активності — ділянка занедбана"
        elif viirs < 1.5:
            viirs_score, viirs_label = 1.0, "Низька нічна активність для забудови"
        else:
            viirs_score, viirs_label = 0.0, "Норма для забудови"
    else:
        viirs_score, viirs_label = 0.0, "Норма"

    breakdown["VIIRS (нічна активність)"] = (viirs_score, f"{viirs:.2f} нВт — {viirs_label}")
    total += viirs_score

    # ── 4. SAR (0–1 балів) ────────────────────────────────────────────────
    if is_agri:
        # С/г: зміна поверхні = підозріле будівництво
        sar_score = 1.0 if sar_changed else 0.0
        sar_label = "Зміну поверхні виявлено на с/г ділянці" if sar_changed else "Поверхня стабільна"
    elif is_built:
        # Забудова: зміна поверхні = нормальне будівництво/ремонт
        sar_score = 0.0
        sar_label = "Будівельна активність (норма)" if sar_changed else "Поверхня стабільна"
    else:
        sar_score = 0.5 if sar_changed else 0.0
        sar_label = "Зміну виявлено" if sar_changed else "Стабільна"

    breakdown["SAR (зміна поверхні)"] = (sar_score, sar_label)
    total += sar_score

    # ── 5. Площа (0–1 балів) ─────────────────────────────────────────────
    area_score = min(area_ha / 20.0, 1.0)
    breakdown["Площа активу"] = (round(area_score, 1), f"{area_ha} га")
    total += area_score

    total = min(round(total, 1), 10.0)

    # ── Рівень ───────────────────────────────────────────────────────────
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
        score=total, label=label, color=color,
        emoji=emoji, summary=summary, breakdown=breakdown,
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

    is_agri  = land_type in ("Сільське господарство", "Пасовище")
    is_built = land_type in ("Забудова", "Промисловість")
    rows = []

    # ── Землекористування ────────────────────────────────────────────────
    if is_agri:
        if ndbi > 0.1:
            sat_use = "Забудова / тверде покриття"
            status  = "🚨 Розбіжність"
        elif ndvi < 0.2:
            sat_use = "Незадіяна / закинута"
            status  = "⚠️ Не відповідає"
        else:
            sat_use = land_type
            status  = "✅ Відповідає"
    elif is_built:
        if ndvi > 0.4 and ndbi < 0.05:
            sat_use = "Можлива занедбаність / незабудована"
            status  = "⚠️ Не відповідає"
        else:
            sat_use = land_type
            status  = "✅ Відповідає"
    else:
        sat_use = land_type
        status  = "✅ Відповідає"
    rows.append(["Землекористування", land_type, sat_use, status])

    # ── Рослинність ──────────────────────────────────────────────────────
    if is_agri:
        official_veg = "Очікується (NDVI > 0.35)"
        sat_veg = f"NDVI = {ndvi:.3f}"
        veg_status = (
            "✅ Норма" if ndvi >= 0.35
            else "⚠️ Низька" if ndvi >= 0.2
            else "🚨 Критично низька"
        )
        rows.append(["Рослинність (NDVI)", official_veg, sat_veg, veg_status])
    elif is_built:
        official_veg = "Мінімальна (NDVI < 0.2)"
        sat_veg = f"NDVI = {ndvi:.3f}"
        veg_status = "✅ Норма" if ndvi < 0.3 else "⚠️ Заростає — можлива занедбаність"
        rows.append(["Рослинність (NDVI)", official_veg, sat_veg, veg_status])

    # ── Нічна активність ─────────────────────────────────────────────────
    if is_agri:
        official_night = "Не очікується"
        night_status   = "🚨 Виявлено" if viirs > 2.0 else "✅ Відсутня"
    elif is_built:
        official_night = "Очікується (освітлення, активність)"
        night_status   = "✅ Норма" if viirs >= 1.5 else "⚠️ Низька — можлива занедбаність"
    else:
        official_night = "Не визначено"
        night_status   = "⚠️ Є активність" if viirs > 2.0 else "✅ Спокійно"

    rows.append([
        "Нічна активність (VIIRS)",
        official_night,
        f"{viirs:.2f} нВт",
        night_status,
    ])

    # ── Зміна поверхні ───────────────────────────────────────────────────
    if is_agri:
        official_sar = "Не очікується"
        sar_status   = "⚠️ Зміна поверхні" if sar_changed else "✅ Стабільна"
    elif is_built:
        official_sar = "Можлива (будівництво / ремонт)"
        sar_status   = "✅ Будівельна активність" if sar_changed else "✅ Стабільна"
    else:
        official_sar = "Не визначено"
        sar_status   = "⚠️ Зміна" if sar_changed else "✅ Стабільна"

    rows.append([
        "Зміна поверхні (SAR)",
        official_sar,
        "Виявлено (Δ > 3 dB)" if sar_changed else "Не виявлено",
        sar_status,
    ])

    return pd.DataFrame(rows, columns=["Параметр", "📋 Кадастр", "🛰️ Супутник", "Статус"])


# ─────────────────────────────────────────────
# Demo кейси (pre-loaded)
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