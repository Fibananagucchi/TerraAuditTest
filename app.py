"""
TerraAudit — Streamlit Dashboard
Головний файл додатку.
"""

import os
from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
import plotly.express as px

import price_corridor
import budget_optimizer
import llm_teaser
import geoai_engine

# ─────────────────────────────────────────────
# Конфігурація сторінки
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="TerraAudit | Asset Discovery",
    layout="wide",
    page_icon="🛰️",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .stTabs [data-baseweb="tab"] { font-size: 0.95rem; font-weight: 600; }
    .metric-box {
        background: #f0f4ff; border-radius: 10px;
        padding: 1rem; margin-bottom: 0.5rem;
    }
    .flag-box {
        background: #fff8e1; border-left: 4px solid #f5a623;
        padding: 0.6rem 1rem; border-radius: 4px; margin: 0.3rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# session_state — зберігає результати між перемиканнями табів
# ─────────────────────────────────────────────

def _init_state():
    defaults = {
        "sat_data":      None,   # результат analyze_satellite_data
        "ndvi_df":       None,   # NDVI часовий ряд
        "viirs_df":      None,   # VIIRS часовий ряд
        "scan_done":     False,
        "current_lat":   50.4501,
        "current_lon":   30.5234,
        "full_address":  "Київ (за замовчуванням)",
        "teaser_text":   None,
        "min_p":         0,
        "max_p":         0,
        "median_p":      0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ─────────────────────────────────────────────
# ЗАГОЛОВОК
# ─────────────────────────────────────────────

st.title("🛰️ TerraAudit: Супутниковий Аудит Громад")
st.markdown(
    "Виявлення нереалізованих земельних активів через Earth Observation "
    "(Sentinel-1/2, VIIRS) та відкриті дані Прозорро.Продажі."
)
st.divider()


# ─────────────────────────────────────────────
# САЙДБАР — параметри ділянки
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Параметри ділянки")

    address_query = st.text_input(
        "Локація (місто, вулиця або громада)",
        value="Черкаси, вул. Хрещатик",
    )

    if st.button("📍 Знайти на карті", use_container_width=True):
        lat, lon, addr = geoai_engine.get_coordinates_by_address(address_query)
        if lat:
            st.session_state.current_lat   = lat
            st.session_state.current_lon   = lon
            st.session_state.full_address  = addr
            st.session_state.scan_done     = False  # скинути попередній скан
            st.success("✅ Знайдено!")
        else:
            st.error("❌ Локацію не знайдено. Спробуйте інакше.")

    st.caption(f"📌 {st.session_state.full_address[:60]}...")

    st.divider()

    area_ha = st.number_input(
        "Площа за кадастром (га)", min_value=0.1, value=5.0, step=0.5
    )

    land_type = st.selectbox(
        "Кадастрове призначення",
        ["Сільське господарство", "Пасовище", "Забудова", "Промисловість"],
    )

    start_year = st.selectbox("Аналіз від року", [2020, 2021, 2022, 2023], index=1)

    st.divider()

    # Статуси систем
    st.markdown("**📡 Статус систем**")
    if geoai_engine.EE_IS_ACTIVE:
        st.success("Google Earth Engine: Live")
    else:
        st.warning("GEE: Demo-режим")
        st.caption("Запустіть `python auth.py` для підключення")

    groq_ok = bool(os.environ.get("GROQ_API_KEY"))
    if groq_ok:
        st.success("Groq LLM: Підключено")
    else:
        st.error("Groq LLM: Немає ключа")

    st.info("Прозорро.Продажі: API активно")


# ─────────────────────────────────────────────
# ОБЧИСЛЕННЯ ЦІНОВОГО КОРИДОРУ
# (рахується при зміні параметрів, не лише при скані)
# ─────────────────────────────────────────────

min_p, max_p, median_p = price_corridor.calculate_corridor(area_ha, land_type)
st.session_state.min_p    = min_p
st.session_state.max_p    = max_p
st.session_state.median_p = median_p


# ─────────────────────────────────────────────
# ТАБИ
# ─────────────────────────────────────────────

tab_geo, tab_price, tab_budget, tab_teaser = st.tabs([
    "🛰️ 1. GeoAI (Супутник)",
    "💰 2. Ціновий коридор",
    "📊 3. Бюджет громади",
    "📄 4. Інвестиційний тізер",
])


# ══════════════════════════════════════════════
# ТАБ 1: GeoAI
# ══════════════════════════════════════════════

with tab_geo:
    st.markdown("### Мультиспектральний аналіз ділянки")

    map_col, ctrl_col = st.columns([2, 1])

    # Карта
    with map_col:
        m = folium.Map(
            location=[st.session_state.current_lat, st.session_state.current_lon],
            zoom_start=14,
            tiles="OpenStreetMap",
        )
        folium.Circle(
            [st.session_state.current_lat, st.session_state.current_lon],
            radius=300,
            color="#e74c3c",
            fill=True,
            fill_opacity=0.25,
            tooltip="Зона аналізу (300 м)",
        ).add_to(m)
        folium.Marker(
            [st.session_state.current_lat, st.session_state.current_lon],
            tooltip=st.session_state.full_address[:50],
        ).add_to(m)
        st_folium(m, width=620, height=380, returned_objects=[])

    # Кнопка сканування + результати
    with ctrl_col:
        st.markdown("**Дані для аналізу:**")
        st.markdown(f"- 📐 Площа: **{area_ha} га**")
        st.markdown(f"- 🗂️ Тип: **{land_type}**")
        st.markdown(f"- 📅 Період: **{start_year} – 2024**")
        st.markdown(
            f"- 🌍 Режим: **{'🟢 Live GEE' if geoai_engine.EE_IS_ACTIVE else '🟡 Demo'}**"
        )

        if st.button("🚀 Запустити супутниковий скан", type="primary", use_container_width=True):
            with st.spinner("Обробка супутникових даних…"):
                # Snapshot
                sat = geoai_engine.analyze_satellite_data(
                    st.session_state.current_lat,
                    st.session_state.current_lon,
                )
                # NDVI часовий ряд
                ndvi_df = geoai_engine.get_ndvi_timeseries(
                    st.session_state.current_lat,
                    st.session_state.current_lon,
                    start_year=start_year,
                )
                # VIIRS
                viirs_df = geoai_engine.get_viirs_nightlights(
                    st.session_state.current_lat,
                    st.session_state.current_lon,
                    start_year=start_year,
                )

            st.session_state.sat_data  = sat
            st.session_state.ndvi_df   = ndvi_df
            st.session_state.viirs_df  = viirs_df
            st.session_state.scan_done = True

        # Результати snapshot
        if st.session_state.scan_done and st.session_state.sat_data:
            sat = st.session_state.sat_data
            st.divider()
            st.markdown("**📡 Телеметрія:**")

            # NDVI
            ndvi = sat["ndvi_score"]
            if ndvi < 0.2 and land_type in ["Сільське господарство", "Пасовище"]:
                st.error(f"NDVI: **{ndvi:.3f}** — аномально низький для {land_type}")
            else:
                st.success(f"NDVI: **{ndvi:.3f}** — у нормі")

            # NDBI
            ndbi = sat["ndbi_score"]
            if ndbi > 0.05:
                st.warning(f"NDBI: **{ndbi:.3f}** — ознаки твердого покриття")
            else:
                st.success(f"NDBI: **{ndbi:.3f}** — природна поверхня")

            # VIIRS
            viirs = sat["night_light_rad"]
            if viirs > 2.5:
                st.error(f"VIIRS: **{viirs:.2f}** нВт — нічна активність на 'пустирі'")
            elif viirs > 1.0:
                st.warning(f"VIIRS: **{viirs:.2f}** нВт — помірна активність")
            else:
                st.success(f"VIIRS: **{viirs:.2f}** нВт — тихо")

            # SAR
            if sat["sar_detected_changes"]:
                st.warning(
                    f"SAR Δ: **{sat['sar_delta_db']:+.1f} dB** — "
                    "зміна поверхні (земляні роботи?)"
                )
            else:
                st.success(f"SAR Δ: **{sat['sar_delta_db']:+.1f} dB** — поверхня стабільна")

            if sat.get("is_demo"):
                st.caption("⚠️ Дані синтетичні (demo-режим)")

    # ── NDVI Часовий ряд ──
    st.divider()
    st.markdown("### 📈 NDVI / NDBI — зміна в часі")

    if st.session_state.scan_done and st.session_state.ndvi_df is not None:
        ndvi_df  = st.session_state.ndvi_df
        viirs_df = st.session_state.viirs_df

        c1, c2 = st.columns(2)

        with c1:
            # NDVI + NDBI на одному графіку
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=ndvi_df["date"], y=ndvi_df["NDVI"],
                name="NDVI (рослинність)",
                line=dict(color="#27ae60", width=2),
                fill="tozeroy", fillcolor="rgba(39,174,96,0.1)",
            ))
            if "NDBI" in ndvi_df.columns:
                fig.add_trace(go.Scatter(
                    x=ndvi_df["date"], y=ndvi_df["NDBI"],
                    name="NDBI (забудова)",
                    line=dict(color="#e74c3c", width=2, dash="dot"),
                ))
            # Референсні лінії
            fig.add_hline(y=0.3, line_dash="dash", line_color="orange",
                          annotation_text="Мін. норма с/г (0.3)")
            fig.add_hline(y=0.0, line_color="gray", line_width=0.5)
            fig.update_layout(
                title="Sentinel-2: NDVI та NDBI (2021–2024)",
                xaxis_title="Дата",
                yaxis_title="Індекс",
                legend=dict(orientation="h", y=-0.2),
                height=350,
                margin=dict(t=40, b=60),
            )
            st.plotly_chart(fig, use_container_width=True)
            src = ndvi_df["source"].iloc[0] if "source" in ndvi_df.columns else ""
            st.caption(f"Джерело: {src}")

        with c2:
            # VIIRS нічна активність
            if viirs_df is not None and len(viirs_df) > 0:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=viirs_df["date"],
                    y=viirs_df["avg_radiance"],
                    name="Нічна яскравість",
                    marker_color=[
                        "#e74c3c" if v > 2.5 else "#f39c12" if v > 1.0 else "#3498db"
                        for v in viirs_df["avg_radiance"]
                    ],
                ))
                fig2.add_hline(y=2.5, line_dash="dash", line_color="red",
                               annotation_text="Поріг аномалії")
                fig2.update_layout(
                    title="VIIRS: Нічна активність (нВт/см²/ср)",
                    xaxis_title="Місяць",
                    yaxis_title="Яскравість",
                    height=350,
                    margin=dict(t=40, b=60),
                    showlegend=False,
                )
                st.plotly_chart(fig2, use_container_width=True)
                src2 = viirs_df["source"].iloc[0] if "source" in viirs_df.columns else ""
                st.caption(f"Джерело: {src2}")
    else:
        st.info("👆 Натисніть «Запустити супутниковий скан» щоб побачити часові ряди.")


# ══════════════════════════════════════════════
# ТАБ 2: Ціновий коридор
# ══════════════════════════════════════════════

with tab_price:
    st.markdown("### Динамічний ціновий коридор")
    st.markdown(
        "Статистичний аналіз цін завершених аукціонів **Прозорро.Продажі** "
        "для ділянок аналогічного типу."
    )

    # Метрики
    m1, m2, m3 = st.columns(3)
    m1.metric("25-й перцентиль (мін.)",   f"{min_p:,.0f} грн/рік", help="Нижня межа коридору")
    m2.metric("Медіана (справедлива ціна)", f"{median_p:,.0f} грн/рік", delta="ринковий орієнтир")
    m3.metric("85-й перцентиль (макс.)",   f"{max_p:,.0f} грн/рік", help="Верхня межа коридору")

    st.divider()

    # ── Демо-повзунок для пітчу ──
    st.markdown("#### 🎮 Симуляція аукціону (демо для пітчу)")
    st.markdown(
        "Судді можуть рухати повзунок — система миттєво реагує."
    )

    slider_max = int(max_p * 1.8) if max_p > 0 else 100_000
    slider_val = int(median_p) if median_p > 0 else slider_max // 2

    proposed = st.slider(
        "Запропонована ціна оренди (грн/рік):",
        min_value=0,
        max_value=slider_max,
        value=slider_val,
        step=1000,
        format="%d грн",
    )

    verdict = price_corridor.price_verdict(proposed, min_p, max_p, median_p)

    # Візуальний відгук
    if verdict["verdict"] == "suspicious_low":
        st.error(verdict["message"])
        st.markdown(
            f"**Потенційні втрати бюджету:** "
            f"{(median_p - proposed):,.0f} грн/рік "
            f"({abs(verdict['deviation_pct']):.1f}% нижче медіани)"
        )
    elif verdict["verdict"] == "suspicious_high":
        st.warning(verdict["message"])
    elif verdict["verdict"] == "fair":
        st.success(verdict["message"])
    else:
        st.info(verdict["message"])

    # Графік коридору
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=["Мін. ринок", "Медіана", "Макс. ринок", "Пропозиція"],
        y=[min_p, median_p, max_p, proposed],
        marker_color=[
            "#3498db", "#27ae60", "#3498db",
            "#e74c3c" if verdict["verdict"] == "suspicious_low"
            else "#27ae60" if verdict["verdict"] == "fair"
            else "#f39c12"
        ],
        text=[f"{v:,.0f}" for v in [min_p, median_p, max_p, proposed]],
        textposition="outside",
    ))
    fig_bar.update_layout(
        title="Ціновий коридор vs пропозиція аукціону",
        yaxis_title="грн/рік",
        height=350,
        showlegend=False,
        margin=dict(t=40),
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.caption("Дані: Прозорро.Продажі API + НБУ курс USD/UAH")


# ══════════════════════════════════════════════
# ТАБ 3: Бюджет громади
# ══════════════════════════════════════════════

with tab_budget:
    st.markdown("### Оптимальний розподіл бюджету громади")
    st.markdown(
        "LP-модель розподіляє вивільнені кошти від монетизації активу "
        "між соціальними пріоритетами (PuLP / CBC solver)."
    )

    budget_input = st.number_input(
        "Вивільнений річний дохід (грн):",
        min_value=0,
        value=int(median_p) if median_p > 0 else 100_000,
        step=10_000,
        format="%d",
    )

    result = budget_optimizer.optimize_budget(total_funds=budget_input)

    # Метрики
    b1, b2, b3 = st.columns(3)
    b1.metric("🏫 Школи",    f"{result['Школи (грн)']:,.0f} грн")
    b2.metric("🛣️ Дороги",   f"{result['Дороги (грн)']:,.0f} грн")
    b3.metric("🏥 Медицина", f"{result['Медицина (грн)']:,.0f} грн")

    # Pie chart
    categories = ["Школи", "Дороги", "Медицина"]
    values = [
        result["Школи (грн)"],
        result["Дороги (грн)"],
        result["Медицина (грн)"],
    ]

    fig_pie = px.pie(
        names=categories,
        values=values,
        color_discrete_sequence=["#3498db", "#e67e22", "#e74c3c"],
        hole=0.4,
    )
    fig_pie.update_layout(
        title="Розподіл бюджету (оптимальний за соціальною корисністю)",
        height=380,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.caption(
        f"Статус солвера: **{result.get('Статус', 'N/A')}** | "
        f"Розподілено: **{result.get('Всього (грн)', 0):,.0f} грн** з **{budget_input:,.0f} грн**"
    )


# ══════════════════════════════════════════════
# ТАБ 4: Інвестиційний тізер
# ══════════════════════════════════════════════

with tab_teaser:
    st.markdown("### Інвестиційний тізер для Прозорро.Продажі")
    st.markdown(
        "LLM (Groq / llama-3.3-70b) генерує готовий тізер на основі "
        "даних ділянки та супутникового аналізу."
    )

    # Додаткові параметри тізера
    with st.expander("⚙️ Параметри генерації", expanded=False):
        custom_notes = st.text_area(
            "Додаткові відомості про ділянку (опційно):",
            placeholder="Наприклад: поруч є залізнична станція, під'їзна дорога асфальтована...",
            height=80,
        )

    col_btn, col_status = st.columns([1, 2])

    with col_btn:
        gen_btn = st.button(
            "✨ Згенерувати тізер",
            type="primary",
            use_container_width=True,
            disabled=not groq_ok,
        )
        if not groq_ok:
            st.caption("⚠️ Додайте GROQ_API_KEY у .env")

    if gen_btn and groq_ok:
        sat = st.session_state.sat_data

        with st.spinner("Groq генерує тізер…"):
            teaser = llm_teaser.generate_teaser(
                community_name=address_query,
                area=area_ha,
                land_type=land_type,
                market_price=median_p,
                ndvi_score=sat["ndvi_score"] if sat else None,
                viirs_rad=sat["night_light_rad"] if sat else None,
                sar_changed=sat["sar_detected_changes"] if sat else False,
            )
        st.session_state.teaser_text = teaser

    if st.session_state.teaser_text:
        st.divider()
        st.markdown(st.session_state.teaser_text)
        st.divider()
        st.download_button(
            "⬇️ Завантажити тізер (.md)",
            data=st.session_state.teaser_text,
            file_name="terraaudit_teaser.md",
            mime="text/markdown",
        )