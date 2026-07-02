"""
TerraAudit — Streamlit Dashboard v4
Dark space theme: deep navy + teal scan accent.
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
import analysis
import report

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="TerraAudit",
    layout="wide",
    page_icon="🛰️",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Design system
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ── */
.stApp { background: #080E1C !important; }
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif !important; }
.main .block-container { padding: 1.2rem 2rem 2rem 2rem !important; max-width: 1400px; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #0B1425 !important;
    border-right: 1px solid rgba(0,212,170,0.12) !important;
}
section[data-testid="stSidebar"] .block-container { padding: 1.5rem 1rem !important; }
section[data-testid="stSidebar"] label {
    color: #6B7FA3 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span { color: #C8D4E8 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color: #E8EDF5 !important; }

/* ── Headings ── */
h1,h2,h3,h4 { font-family:'Space Grotesk',sans-serif !important; color:#E8EDF5 !important; font-weight:700 !important; }
p, li, span { color: #B0BDD4 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #0B1425 !important;
    border-radius: 10px !important;
    padding: 5px !important;
    gap: 3px !important;
    border: 1px solid #1A2E4A !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6B7FA3 !important;
    border-radius: 7px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.82rem !important;
    padding: 0.45rem 1rem !important;
    border: none !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: #0F2040 !important;
    color: #00D4AA !important;
    border: 1px solid rgba(0,212,170,0.25) !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.2rem !important; }

/* ── Buttons ── */
.stButton > button,
.stButton > button > div,
.stButton > button > div > p,
.stButton > button p,
.stButton > button span {
    color: #FFFFFF !important;
}
.stButton > button {
    background: linear-gradient(135deg, #00B894 0%, #008F75 100%) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    letter-spacing: 0.04em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 2px 16px rgba(0,184,148,0.25) !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00C9A7 0%, #00A884 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 22px rgba(0,184,148,0.4) !important;
}
.stDownloadButton > button,
.stDownloadButton > button > div,
.stDownloadButton > button > div > p,
.stDownloadButton > button p {
    color: #E0EAF5 !important;
    background: #0D1E38 !important;
    border: 1px solid #2A4A70 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
.stDownloadButton > button:hover {
    background: #132840 !important;
    border-color: rgba(0,184,148,0.6) !important;
    color: #FFFFFF !important;
}

/* ── Inputs ── */
.stTextInput input, .stNumberInput input {
    background: #0B1425 !important;
    border: 1px solid #1A2E4A !important;
    border-radius: 8px !important;
    color: #E8EDF5 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: rgba(0,212,170,0.5) !important;
    box-shadow: 0 0 0 2px rgba(0,212,170,0.1) !important;
}
.stSelectbox > div > div {
    background: #0B1425 !important;
    border: 1px solid #1A2E4A !important;
    border-radius: 8px !important;
    color: #E8EDF5 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #0B1425 !important;
    border: 1px solid #1A2E4A !important;
    border-radius: 10px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] > div {
    color: #6B7FA3 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stMetricValue"] > div {
    color: #E8EDF5 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.3rem !important;
}
[data-testid="stMetricDelta"] > div { font-size: 0.75rem !important; }

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 8px !important; border: none !important; }
div[data-baseweb="notification"] { border-radius: 8px !important; }

/* ── Expander ── */
details {
    background: #0B1425 !important;
    border: 1px solid #1A2E4A !important;
    border-radius: 10px !important;
    overflow: hidden;
}
details summary {
    color: #C8D4E8 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 600 !important;
    padding: 0.8rem 1rem !important;
}
details > div { background: #0B1425 !important; padding: 0 1rem 1rem !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1A2E4A !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── Divider ── */
hr { border-color: #1A2E4A !important; margin: 1.2rem 0 !important; }

/* ── Slider ── */
[data-testid="stSlider"] > div > div > div {
    background: linear-gradient(90deg,#00D4AA,#00A896) !important;
}
/* Fix slider min/max labels — remove green background */
[data-testid="stSlider"] div[data-testid="stTickBarMin"],
[data-testid="stSlider"] div[data-testid="stTickBarMax"],
[data-testid="stSlider"] > div > div > div:first-child,
[data-testid="stSlider"] > div > div > div:last-child,
[data-testid="stSlider"] span {
    background: transparent !important;
    background-image: none !important;
    color: #6B7FA3 !important;
}

/* ── Progress ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg,#00D4AA,#0097A7) !important;
}

/* ── Caption ── */
.stCaption { color: #3D5070 !important; }

/* ── Custom components ── */
.ta-header {
    background: linear-gradient(135deg, #0B1425 0%, #0F1F3D 100%);
    border: 1px solid rgba(0,212,170,0.15);
    border-radius: 14px;
    padding: 1.4rem 2rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.ta-header::before {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 60%; height: 2px;
    background: linear-gradient(90deg,transparent,#00D4AA,transparent);
    animation: scan 3s ease-in-out infinite;
}
@keyframes scan {
    0%   { left: -60%; }
    100% { left: 120%; }
}
.ta-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #E8EDF5;
    letter-spacing: -0.02em;
    line-height: 1;
}
.ta-logo span { color: #00D4AA; }
.ta-tagline {
    font-size: 0.82rem;
    color: #6B7FA3;
    margin-top: 0.3rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.ta-breadcrumb {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #3D5070;
    margin-top: 0.8rem;
}
.ta-breadcrumb span { color: #00D4AA; }

.ta-status-row {
    display: flex; gap: 0.5rem; margin-top: 0.8rem; flex-wrap: wrap;
}
.ta-badge {
    display: inline-flex; align-items: center; gap: 0.35rem;
    background: rgba(0,212,170,0.08);
    border: 1px solid rgba(0,212,170,0.2);
    border-radius: 20px;
    padding: 0.2rem 0.7rem;
    font-size: 0.72rem;
    color: #00D4AA;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 500;
}
.ta-badge.warn {
    background: rgba(245,166,35,0.08);
    border-color: rgba(245,166,35,0.25);
    color: #F5A623;
}
.ta-badge.err {
    background: rgba(255,75,75,0.08);
    border-color: rgba(255,75,75,0.2);
    color: #FF6B6B;
}
.ta-dot {
    width: 6px; height: 6px; border-radius: 50%;
    background: #00D4AA;
    box-shadow: 0 0 6px #00D4AA;
    animation: pulse-dot 2s ease-in-out infinite;
    display: inline-block;
}
.ta-dot.warn { background: #F5A623; box-shadow: 0 0 6px #F5A623; }
.ta-dot.off  { background: #FF6B6B; box-shadow: 0 0 6px #FF6B6B; animation: none; }
@keyframes pulse-dot {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.5; transform:scale(0.7); }
}

.ta-score-card {
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    margin: 0.8rem 0;
    display: flex; align-items: center; gap: 1.2rem;
    border: 1px solid;
    position: relative;
    overflow: hidden;
}
.ta-score-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: rgba(0,0,0,0.55);
    border-radius: inherit;
}
.ta-score-card > * { position: relative; z-index: 1; }
.ta-score-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 3rem; font-weight: 700;
    line-height: 1; white-space: nowrap;
}
.ta-score-lbl { font-size: 1rem; font-weight: 600; color: #E8EDF5; }
.ta-score-sum { font-size: 0.82rem; color: #B0BDD4; margin-top: 0.25rem; line-height: 1.4; }

.ta-sat-grid {
    display: grid; grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 0.6rem; margin-top: 0.4rem; margin-bottom: 0.6rem;
}
.ta-sat-cell {
    background: #080E1C;
    border: 1px solid #1A2E4A;
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
}
.ta-sat-label {
    font-size: 0.68rem; color: #6B7FA3;
    text-transform: uppercase; letter-spacing: 0.07em;
    font-family: 'Space Grotesk', sans-serif;
}
.ta-sat-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.05rem; font-weight: 500;
    color: #E8EDF5; margin-top: 0.2rem;
}
.ta-sat-status {
    font-size: 0.7rem; margin-top: 0.15rem;
}
.ok   { color: #00D4AA !important; }
.warn { color: #F5A623 !important; }
.err  { color: #FF6B6B !important; }

.ta-sidebar-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.3rem; font-weight: 700;
    color: #E8EDF5; letter-spacing: -0.01em;
    margin-bottom: 0.2rem;
}
.ta-sidebar-logo span { color: #00D4AA; }
.ta-sidebar-sub {
    font-size: 0.68rem; color: #3D5070;
    text-transform: uppercase; letter-spacing: 0.1em;
}
.ta-section-label {
    font-size: 0.68rem; color: #3D5070;
    text-transform: uppercase; letter-spacing: 0.1em;
    font-weight: 600; margin: 1rem 0 0.4rem 0;
    font-family: 'Space Grotesk', sans-serif;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────

def _init():
    defaults = {
        "sat_data": None, "ndvi_df": None, "viirs_df": None,
        "asset_score": None, "comparison_df": None, "prozorro_df": None,
        "scan_done": False, "lat": 50.4501, "lon": 30.5234,
        "address": "Київ (за замовчуванням)", "area_ha": 5.0,
        "land_type": "Сільське господарство", "teaser_text": None,
        "min_p": 0, "max_p": 0, "median_p": 0, "budget_result": None,
        "sat_data_b": None, "year_a": None, "year_b": None, "compare_done": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ─────────────────────────────────────────────
# Plotly dark theme helper
# ─────────────────────────────────────────────

PLOTLY_DARK = dict(
    paper_bgcolor="#080E1C",
    plot_bgcolor="#0B1425",
    font=dict(family="Space Grotesk", color="#B0BDD4", size=11),
    xaxis=dict(gridcolor="#1A2E4A", linecolor="#1A2E4A", tickcolor="#3D5070"),
    yaxis=dict(gridcolor="#1A2E4A", linecolor="#1A2E4A", tickcolor="#3D5070"),
    margin=dict(t=44, b=40, l=10, r=10),
)


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

with st.sidebar:
    from datetime import datetime as _dt
    _cur_year = _dt.now().year
    _last_full_year = _cur_year - 1  # поточний рік неповний
    _years = list(range(2020, _last_full_year + 1))
    _default_idx = _years.index(2021) if 2021 in _years else 1
    # Define start_year here so it's available for demo case block below
    start_year = _years[_default_idx]

    st.markdown("""
    <div class="ta-sidebar-logo">TERRA<span>AUDIT</span></div>
    <div class="ta-sidebar-sub">Satellite Asset Intelligence</div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown('<div class="ta-section-label">Швидкий старт</div>', unsafe_allow_html=True)
    demo_choice = st.selectbox(
        "Demo кейс",
        ["— обрати —"] + list(analysis.DEMO_CASES.keys()),
        key="demo_select", label_visibility="collapsed",
    )

    if demo_choice != "— обрати —":
        case = analysis.DEMO_CASES[demo_choice]
        if st.button("Завантажити кейс", use_container_width=True):
            st.session_state.lat       = case["lat"]
            st.session_state.lon       = case["lon"]
            st.session_state.area_ha   = case["area_ha"]
            st.session_state.land_type = case["land_type"]
            st.session_state.address   = case["address"]

            if geoai_engine.EE_IS_ACTIVE:
                # GEE підключено — отримуємо реальні супутникові дані
                with st.spinner("Отримання реальних даних з GEE…"):
                    sat = geoai_engine.analyze_satellite_data(
                        case["lat"], case["lon"], year=start_year
                    )
                    ndvi_df = geoai_engine.get_ndvi_timeseries(
                        case["lat"], case["lon"], start_year=start_year
                    )
                    viirs_df = geoai_engine.get_viirs_nightlights(
                        case["lat"], case["lon"], start_year=start_year
                    )
            else:
                # Demo режим — синтетичні дані
                sat      = case["sat_data"]
                ndvi_df  = geoai_engine._demo_ndvi_timeseries(2021, 2024)
                viirs_df = geoai_engine._demo_viirs(2021, 2024)

            st.session_state.sat_data  = sat
            st.session_state.ndvi_df   = ndvi_df
            st.session_state.viirs_df  = viirs_df
            st.session_state.asset_score = analysis.calculate_asset_score(
                sat["ndvi_score"], sat["ndbi_score"], sat["night_light_rad"],
                sat["sar_detected_changes"], case["land_type"], case["area_ha"],
            )
            st.session_state.comparison_df = analysis.build_comparison_table(
                case["land_type"], sat["ndvi_score"], sat["ndbi_score"],
                sat["night_light_rad"], sat["sar_detected_changes"],
            )
            st.session_state.scan_done = True
            st.rerun()

    st.divider()

    st.markdown('<div class="ta-section-label">Власна ділянка</div>', unsafe_allow_html=True)
    address_input = st.text_input("Локація", value=st.session_state.address, label_visibility="collapsed", placeholder="Місто, вулиця або громада…")

    st.caption("Адреса або координати: 49.444, 31.998")
    if st.button("Знайти на карті", use_container_width=True):
        # Try coordinate parsing first: "49.444, 31.998" or "49.444 31.998"
        import re
        coord_match = re.match(
            r"^\s*(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)\s*$",
            address_input.strip()
        )
        if coord_match:
            lat = float(coord_match.group(1))
            lon = float(coord_match.group(2))
            st.session_state.lat = lat
            st.session_state.lon = lon
            st.session_state.address = f"Координати: {lat:.4f}, {lon:.4f}"
            st.session_state.scan_done = False
            st.success("✅ Координати розпізнано")
        else:
            lat, lon, addr = geoai_engine.get_coordinates_by_address(address_input)
            if lat:
                st.session_state.lat = lat; st.session_state.lon = lon
                st.session_state.address = addr; st.session_state.scan_done = False
                st.success("✅ Знайдено")
            else:
                st.error("Не знайдено. Спробуйте координати: 49.444, 31.998")

    area_ha = st.number_input("Площа (га)", min_value=0.1, value=float(st.session_state.area_ha), step=0.5)
    st.session_state.area_ha = area_ha

    land_type = st.selectbox(
        "Тип",
        ["Сільське господарство", "Пасовище", "Забудова", "Промисловість"],
        index=["Сільське господарство","Пасовище","Забудова","Промисловість"].index(st.session_state.land_type),
    )
    st.session_state.land_type = land_type
    start_year = st.selectbox("Аналіз від", _years, index=_years.index(start_year) if start_year in _years else _default_idx)

    st.markdown('<div class="ta-section-label" style="margin-top:0.5rem">Порівняння років</div>', unsafe_allow_html=True)
    col_y1, col_y2 = st.columns(2)
    with col_y1:
        year_a = st.selectbox("Рік A", _years,
            index=max(0, len(_years) - 2),
            label_visibility="visible")
    with col_y2:
        _years_b = [y for y in _years if y != year_a]
        year_b = st.selectbox("Рік B", _years_b,
            index=len(_years_b) - 1,
            label_visibility="visible")

    st.divider()

    # Status badges
    groq_ok = bool(os.environ.get("GROQ_API_KEY"))
    gee_live = geoai_engine.EE_IS_ACTIVE

    gee_cls  = "" if gee_live else "warn"
    gee_dot  = "" if gee_live else "warn"
    gee_txt  = "GEE Live" if gee_live else "GEE Demo"
    groq_cls = "" if groq_ok else "err"
    groq_dot = "" if groq_ok else "off"
    groq_txt = "Groq LLM" if groq_ok else "Groq: no key"

    st.markdown(f"""
    <div class="ta-section-label">Системи</div>
    <div class="ta-status-row">
        <div class="ta-badge {gee_cls}"><span class="ta-dot {gee_dot}"></span>{gee_txt}</div>
        <div class="ta-badge {groq_cls}"><span class="ta-dot {groq_dot}"></span>{groq_txt}</div>
        <div class="ta-badge"><span class="ta-dot"></span>Прозорро API</div>
    </div>
    """, unsafe_allow_html=True)

    if not gee_live:
        st.caption("python auth.py для підключення GEE")


# ─────────────────────────────────────────────
# Pricing (always computed)
# ─────────────────────────────────────────────

min_p, max_p, median_p = price_corridor.calculate_corridor(
    st.session_state.area_ha, st.session_state.land_type
)
st.session_state.min_p = min_p
st.session_state.max_p = max_p
st.session_state.median_p = median_p
st.session_state.budget_result = budget_optimizer.optimize_budget(median_p)


# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

mode_badge = "GEE Live" if gee_live else "Demo mode"
mode_color = "#00D4AA" if gee_live else "#F5A623"

st.markdown(f"""
<div class="ta-header">
    <div class="ta-logo">TERRA<span>AUDIT</span></div>
    <div class="ta-tagline">Satellite Asset Intelligence · ESA Sentinel + NASA VIIRS</div>
    <div class="ta-breadcrumb">
        📍 <span>{st.session_state.address[:70]}</span>
        &nbsp;·&nbsp; {st.session_state.area_ha} га
        &nbsp;·&nbsp; {st.session_state.land_type}
        &nbsp;·&nbsp; <span style="color:{mode_color}">{mode_badge}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DEMO WARNING BANNER
# ─────────────────────────────────────────────

if not gee_live:
    st.markdown("""
    <div style="
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        z-index: 9999;
        background: #1A1200;
        border: 1px solid #F5A623;
        border-left: 4px solid #F5A623;
        border-radius: 10px;
        padding: 0.9rem 1.2rem;
        max-width: 320px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.5);
    ">
        <div style="font-size:0.75rem;font-weight:700;color:#F5A623;letter-spacing:0.06em;margin-bottom:0.35rem">
            DEMO РЕЖИМ
        </div>
        <div style="font-size:0.78rem;color:#C8A96E;line-height:1.5">
            Google Earth Engine не підключено — всі супутникові дані є синтетичними і слугують лише для демонстрації логіки системи.
        </div>
        <div style="font-size:0.72rem;color:#5A4A2A;margin-top:0.5rem">
            Для реальних даних: запустіть <code style="color:#F5A623;background:rgba(245,166,35,0.1);padding:0.1rem 0.3rem;border-radius:3px">python auth.py</code>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tab_geo, tab_price, tab_budget, tab_multi, tab_report = st.tabs([
    "GeoAI · Супутник",
    "Ціновий коридор",
    "Бюджет громади",
    "Кілька ділянок",
    "Звіт & Тізер",
])


# ══════════════════════════════════════════════
# TAB 1 — GeoAI
# ══════════════════════════════════════════════

with tab_geo:
    map_col, ctrl_col = st.columns([3, 1])

    with map_col:
        m = folium.Map(location=[st.session_state.lat, st.session_state.lon], zoom_start=14)
        folium.TileLayer("OpenStreetMap", name="🗺️ Карта").add_to(m)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri", name="🛰️ Супутник",
        ).add_to(m)
        folium.LayerControl(position="topright").add_to(m)
        folium.Circle(
            [st.session_state.lat, st.session_state.lon],
            radius=int(np.sqrt(st.session_state.area_ha * 10000 / np.pi)),
            color="#00D4AA", fill=True, fill_opacity=0.15, weight=2,
            tooltip=f"Зона аналізу (~{st.session_state.area_ha} га)",
        ).add_to(m)
        folium.Marker(
            [st.session_state.lat, st.session_state.lon],
            tooltip=st.session_state.address[:60],
            icon=folium.Icon(color="green", icon="circle", prefix="fa"),
        ).add_to(m)
        st_folium(m, width=None, height=320, returned_objects=[])

    with ctrl_col:
        st.markdown(f"""
        <div style="background:#0B1425;border:1px solid #1A2E4A;border-radius:10px;padding:1rem;margin-bottom:0.8rem">
            <div style="font-size:0.65rem;color:#3D5070;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.7rem;font-weight:600">Параметри сканування</div>
            <table style="width:100%;border-collapse:collapse">
                <tr><td style="color:#3D5070;font-size:0.72rem;padding:0.2rem 0;width:45%">Площа</td>
                    <td style="color:#C8D4E8;font-family:JetBrains Mono,monospace;font-size:0.82rem">{st.session_state.area_ha} га</td></tr>
                <tr><td style="color:#3D5070;font-size:0.72rem;padding:0.2rem 0">Тип</td>
                    <td style="color:#C8D4E8;font-size:0.78rem">{st.session_state.land_type}</td></tr>
                <tr><td style="color:#3D5070;font-size:0.72rem;padding:0.2rem 0">Період</td>
                    <td style="color:#C8D4E8;font-family:JetBrains Mono,monospace;font-size:0.82rem">{start_year} – {_cur_year}</td></tr>
                <tr><td style="color:#3D5070;font-size:0.72rem;padding:0.2rem 0">Режим</td>
                    <td style="color:{'#00C49A' if gee_live else '#F5A623'};font-size:0.78rem;font-weight:600">{'Live GEE' if gee_live else 'Demo'}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Запустити супутниковий скан", type="primary", use_container_width=True):
            with st.spinner("Обробка даних Sentinel…"):
                sat = geoai_engine.analyze_satellite_data(st.session_state.lat, st.session_state.lon, year=start_year)
                ndvi_df = geoai_engine.get_ndvi_timeseries(st.session_state.lat, st.session_state.lon, start_year=start_year, end_year=_last_full_year)
                viirs_df = geoai_engine.get_viirs_nightlights(st.session_state.lat, st.session_state.lon, start_year=start_year, end_year=_last_full_year)
                score = analysis.calculate_asset_score(
                    sat["ndvi_score"], sat["ndbi_score"], sat["night_light_rad"],
                    sat["sar_detected_changes"], st.session_state.land_type, st.session_state.area_ha,
                )
                comp_df = analysis.build_comparison_table(
                    st.session_state.land_type, sat["ndvi_score"], sat["ndbi_score"],
                    sat["night_light_rad"], sat["sar_detected_changes"],
                )
                st.session_state.sat_data = sat; st.session_state.ndvi_df = ndvi_df
                st.session_state.viirs_df = viirs_df; st.session_state.asset_score = score
                st.session_state.comparison_df = comp_df; st.session_state.scan_done = True

        st.markdown("<div style='margin-top:0.5rem'></div>", unsafe_allow_html=True)
        if st.button(f"Порівняти {year_a} vs {year_b}", use_container_width=True):
            with st.spinner(f"Сканування {year_a} і {year_b}…"):
                sat_a = geoai_engine.analyze_satellite_data(st.session_state.lat, st.session_state.lon, year=year_a)
                sat_b = geoai_engine.analyze_satellite_data(st.session_state.lat, st.session_state.lon, year=year_b)
                st.session_state.sat_data   = sat_a
                st.session_state.sat_data_b = sat_b
                st.session_state.year_a     = year_a
                st.session_state.year_b     = year_b
                st.session_state.compare_done = True
                st.session_state.scan_done    = True
                ndvi_df = geoai_engine.get_ndvi_timeseries(st.session_state.lat, st.session_state.lon, start_year=min(year_a, year_b), end_year=max(year_a, year_b))
                viirs_df = geoai_engine.get_viirs_nightlights(st.session_state.lat, st.session_state.lon, start_year=min(year_a, year_b), end_year=max(year_a, year_b))
                score = analysis.calculate_asset_score(
                    sat_b["ndvi_score"], sat_b["ndbi_score"], sat_b["night_light_rad"],
                    sat_b["sar_detected_changes"], st.session_state.land_type, st.session_state.area_ha,
                )
                comp_df = analysis.build_comparison_table(
                    st.session_state.land_type, sat_b["ndvi_score"], sat_b["ndbi_score"],
                    sat_b["night_light_rad"], sat_b["sar_detected_changes"],
                )
                st.session_state.ndvi_df = ndvi_df; st.session_state.viirs_df = viirs_df
                st.session_state.asset_score = score; st.session_state.comparison_df = comp_df


    # ── Asset Score + Telemetry (full width) ──────────────────────────────
    if st.session_state.scan_done and st.session_state.asset_score:
        sc = st.session_state.asset_score

        # One pure HTML block — no Streamlit columns, perfect height alignment
        sat = st.session_state.sat_data
        ndvi = sat["ndvi_score"]; ndbi = sat["ndbi_score"]
        viirs = sat["night_light_rad"]; sar_d = sat["sar_detected_changes"]

        is_agri  = st.session_state.land_type in ("Сільське господарство", "Пасовище")
        is_built = st.session_state.land_type in ("Забудова", "Промисловість")

        if is_agri:
            ndvi_cls  = "err" if ndvi < 0.2 else ("warn" if ndvi < 0.35 else "ok")
            ndbi_cls  = "err" if ndbi > 0.1 else "ok"
            viirs_cls = "err" if viirs > 2.5 else ("warn" if viirs > 1.0 else "ok")
            sar_cls   = "warn" if sar_d else "ok"
            ndvi_txt  = "Норма" if ndvi>=0.35 else ("Низький" if ndvi>=0.2 else "Критично низький")
            ndbi_txt  = "Тверде покриття — аномалія" if ndbi>0.1 else "Норма"
            viirs_txt = "Аномалія" if viirs>2.5 else ("Помірна активність" if viirs>1.0 else "Норма")
            sar_txt   = "Зміна — аномалія" if sar_d else "Стабільна"
        elif is_built:
            ndvi_cls  = "warn" if ndvi > 0.4 else "ok"
            ndbi_cls  = "warn" if ndbi < 0.0 else "ok"
            viirs_cls = "err" if viirs < 0.5 else ("warn" if viirs < 1.5 else "ok")
            sar_cls   = "ok"
            ndvi_txt  = "Заростає" if ndvi>0.4 else "Норма"
            ndbi_txt  = "Норма" if ndbi>0.05 else "Низький для забудови"
            viirs_txt = "Норма" if viirs>=1.5 else ("Низька активність" if viirs>=0.5 else "Занедбана")
            sar_txt   = "Будівельна активність" if sar_d else "Стабільна"
        else:
            ndvi_cls = ndbi_cls = viirs_cls = sar_cls = "ok"
            ndvi_txt = "Норма" if ndvi>=0.3 else "Низький"
            ndbi_txt = "Тверде покриття" if ndbi>0.1 else "Норма"
            viirs_txt = "Активність" if viirs>2.0 else "Норма"
            sar_txt = "Зміна" if sar_d else "Стабільна"

        def _cls_color(cls):
            return {"ok": "#00D4AA", "warn": "#F5A623", "err": "#FF6B6B"}.get(cls, "#B0BDD4")

        st.markdown(f"""
        <div style="display:flex;gap:0.7rem;align-items:stretch;margin-bottom:0.8rem">
            <div style="flex:0 0 200px;background:rgba(0,0,0,0.55);border-radius:10px;
                padding:1rem 1.2rem;border:2px solid {sc.color};display:flex;
                flex-direction:column;justify-content:center;position:relative;overflow:hidden">
                <div style="position:absolute;inset:0;background:{sc.color};opacity:0.18;border-radius:inherit"></div>
                <div style="position:relative;z-index:1">
                <div style="font-family:JetBrains Mono,monospace;font-size:2.4rem;
                    font-weight:700;color:#fff;line-height:1">{sc.score}</div>
                <div style="font-size:0.9rem;font-weight:700;color:#fff;margin-top:0.4rem">{sc.emoji} {sc.label}</div>
                <div style="font-size:0.72rem;color:rgba(255,255,255,0.8);
                    margin-top:0.3rem;line-height:1.4">{sc.summary}</div>
                </div>
            </div>
            <div style="flex:1;display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:0.6rem">
                <div class="ta-sat-cell">
                    <div class="ta-sat-label">NDVI · Sentinel-2</div>
                    <div class="ta-sat-value {ndvi_cls}">{ndvi:.3f}</div>
                    <div class="ta-sat-status {ndvi_cls}">{ndvi_txt}</div>
                </div>
                <div class="ta-sat-cell">
                    <div class="ta-sat-label">NDBI · Sentinel-2</div>
                    <div class="ta-sat-value {ndbi_cls}">{ndbi:.3f}</div>
                    <div class="ta-sat-status {ndbi_cls}">{ndbi_txt}</div>
                </div>
                <div class="ta-sat-cell">
                    <div class="ta-sat-label">VIIRS · NASA/NOAA</div>
                    <div class="ta-sat-value {viirs_cls}">{viirs:.2f}</div>
                    <div class="ta-sat-status {viirs_cls}">{viirs_txt}</div>
                </div>
                <div class="ta-sat-cell">
                    <div class="ta-sat-label">SAR · Sentinel-1</div>
                    <div class="ta-sat-value {sar_cls}">Δ {sat['sar_delta_db']:+.1f} dB</div>
                    <div class="ta-sat-status {sar_cls}">{sar_txt}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top:0.8rem'></div>", unsafe_allow_html=True)
        with st.expander("Деталізація Asset Score", expanded=False):
            rows_html = "".join([
                f"""<div style="display:flex;justify-content:space-between;
                    align-items:center;padding:0.45rem 0;
                    border-bottom:1px solid #1A2E4A">
                    <span style="font-size:0.8rem;color:#8B9BB4">{comp}: {desc}</span>
                    <span style="font-family:JetBrains Mono,monospace;font-size:0.85rem;
                        color:#00D4AA;white-space:nowrap;margin-left:1rem">{val:.1f} б</span>
                </div>"""
                for comp, (val, desc) in sc.breakdown.items()
            ])
            st.markdown(f"<div style='padding:0.2rem 0'>{rows_html}</div>",
                unsafe_allow_html=True)

            st.markdown("<div style='margin-top:0.8rem'></div>", unsafe_allow_html=True)
            # Year comparison panel
            if st.session_state.compare_done and st.session_state.sat_data_b:
                sat_a = st.session_state.sat_data
                sat_b = st.session_state.sat_data_b
                ya    = st.session_state.year_a
                yb    = st.session_state.year_b

                def _delta_color(val):
                    if val > 0.05:  return "#FF6B6B"
                    if val < -0.05: return "#00D4AA"
                    return "#6B7FA3"

                ndvi_d  = sat_b["ndvi_score"]  - sat_a["ndvi_score"]
                viirs_d = sat_b["night_light_rad"] - sat_a["night_light_rad"]
                ndbi_d  = sat_b["ndbi_score"]  - sat_a["ndbi_score"]

                st.markdown(f"""
                <div style="background:#0B1425;border:1px solid #1A2E4A;border-radius:10px;padding:0.9rem 1rem;margin:0.6rem 0">
                    <div style="font-size:0.65rem;color:#3D5070;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.7rem;font-weight:600">
                        Порівняння {ya} → {yb}
                    </div>
                    <table style="width:100%;border-collapse:collapse">
                        <tr style="border-bottom:1px solid #1A2E4A">
                            <td style="color:#6B7FA3;font-size:0.72rem;padding:0.35rem 0">Показник</td>
                            <td style="color:#6B7FA3;font-size:0.72rem;text-align:center">{ya}</td>
                            <td style="color:#6B7FA3;font-size:0.72rem;text-align:center">{yb}</td>
                            <td style="color:#6B7FA3;font-size:0.72rem;text-align:center">Δ</td>
                        </tr>
                        <tr>
                            <td style="color:#B0BDD4;font-size:0.78rem;padding:0.35rem 0">NDVI</td>
                            <td style="font-family:JetBrains Mono;font-size:0.82rem;color:#C8D4E8;text-align:center">{sat_a["ndvi_score"]:.3f}</td>
                            <td style="font-family:JetBrains Mono;font-size:0.82rem;color:#C8D4E8;text-align:center">{sat_b["ndvi_score"]:.3f}</td>
                            <td style="font-family:JetBrains Mono;font-size:0.82rem;color:{_delta_color(ndvi_d)};text-align:center;font-weight:600">{ndvi_d:+.3f}</td>
                        </tr>
                        <tr>
                            <td style="color:#B0BDD4;font-size:0.78rem;padding:0.35rem 0">NDBI</td>
                            <td style="font-family:JetBrains Mono;font-size:0.82rem;color:#C8D4E8;text-align:center">{sat_a["ndbi_score"]:.3f}</td>
                            <td style="font-family:JetBrains Mono;font-size:0.82rem;color:#C8D4E8;text-align:center">{sat_b["ndbi_score"]:.3f}</td>
                            <td style="font-family:JetBrains Mono;font-size:0.82rem;color:{_delta_color(ndbi_d)};text-align:center;font-weight:600">{ndbi_d:+.3f}</td>
                        </tr>
                        <tr>
                            <td style="color:#B0BDD4;font-size:0.78rem;padding:0.35rem 0">VIIRS</td>
                            <td style="font-family:JetBrains Mono;font-size:0.82rem;color:#C8D4E8;text-align:center">{sat_a["night_light_rad"]:.2f}</td>
                            <td style="font-family:JetBrains Mono;font-size:0.82rem;color:#C8D4E8;text-align:center">{sat_b["night_light_rad"]:.2f}</td>
                            <td style="font-family:JetBrains Mono;font-size:0.82rem;color:{_delta_color(viirs_d)};text-align:center;font-weight:600">{viirs_d:+.2f}</td>
                        </tr>
                    </table>
                    <div style="font-size:0.68rem;color:#3D5070;margin-top:0.5rem">
                        Зелений Δ = покращення · Червоний Δ = погіршення / нарощення активності
                    </div>
                </div>
                """, unsafe_allow_html=True)



    # Comparison table
    if st.session_state.scan_done and st.session_state.comparison_df is not None:
        st.divider()
        st.markdown("### Кадастр vs Супутник")

        def _color_status(val):
            if "🚨" in str(val): return "background-color:#2D1515;color:#FF6B6B"
            if "⚠️" in str(val): return "background-color:#2A1F0A;color:#F5A623"
            if "✅" in str(val): return "background-color:#0D2519;color:#00D4AA"
            return "color:#B0BDD4"

        st.dataframe(
            st.session_state.comparison_df.style.map(_color_status, subset=["Статус"]),
            use_container_width=True, hide_index=True,
        )

    # Time series charts
    if st.session_state.scan_done and st.session_state.ndvi_df is not None:
        st.divider()
        st.markdown("### Часові ряди")

        # Chart legend explanation
        st.markdown("""
        <div style="display:flex;gap:2rem;margin-bottom:1rem;flex-wrap:wrap">
            <div style="background:#0B1425;border:1px solid #1A2E4A;border-radius:8px;padding:0.7rem 1rem;flex:1;min-width:240px">
                <div style="font-size:0.68rem;color:#3D5070;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem">NDVI · Індекс рослинності</div>
                <div style="font-size:0.8rem;color:#B0BDD4;line-height:1.5">
                    Показує, наскільки активно земля використовується як сільськогосподарська.
                    Здорове поле — вище <span style="color:#F5A623">0.3</span> з чітким сезонним циклом.
                    Пласка лінія нижче порогу — ділянка <span style="color:#FF6B6B">не обробляється</span>.
                </div>
            </div>
            <div style="background:#0B1425;border:1px solid #1A2E4A;border-radius:8px;padding:0.7rem 1rem;flex:1;min-width:240px">
                <div style="font-size:0.68rem;color:#3D5070;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem">VIIRS · Нічна активність</div>
                <div style="font-size:0.8rem;color:#B0BDD4;line-height:1.5">
                    Вимірює яскравість у нічний час (NASA). Якщо ділянка задекларована як пустка,
                    але вночі <span style="color:#FF6B6B">постійно горить світло</span> — це сигнал прихованої діяльності.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        with c1:
            ndvi_df = st.session_state.ndvi_df
            fig = go.Figure()
            year_colors = ["#00D4AA","#3B82F6","#F5A623","#A855F7"]
            for i, yr in enumerate(sorted(ndvi_df["date"].dt.year.unique())):
                ydf = ndvi_df[ndvi_df["date"].dt.year == yr]
                fig.add_trace(go.Scatter(
                    x=ydf["date"], y=ydf["NDVI"], name=str(yr),
                    line=dict(color=year_colors[i % len(year_colors)], width=2),
                    mode="lines+markers", marker=dict(size=4),
                ))
            if "NDBI" in ndvi_df.columns:
                fig.add_trace(go.Scatter(
                    x=ndvi_df["date"], y=ndvi_df["NDBI"], name="NDBI",
                    line=dict(color="#FF6B6B", width=1.5, dash="dot"), opacity=0.7,
                ))
            if is_agri:
                fig.add_hline(y=0.3, line_dash="dash", line_color="#F5A623",
                              annotation_text="Норма с/г", annotation_font_color="#F5A623")
            fig.add_hrect(y0=-0.2, y1=0.2, fillcolor="#FF6B6B", opacity=0.04)
            fig.update_layout(title="Sentinel-2 · NDVI / NDBI", height=340,
                              legend=dict(orientation="h", y=-0.3, bgcolor="rgba(0,0,0,0)"),
                              **PLOTLY_DARK)
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Джерело: ESA Sentinel-2 via Google Earth Engine")

        with c2:
            viirs_df = st.session_state.viirs_df
            if viirs_df is not None and len(viirs_df) > 0:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=viirs_df["date"], y=viirs_df["avg_radiance"],
                    marker_color=[
                        # С/г: висока = аномалія (червоний), низька = норма (зелений)
                        # Забудова: висока = норма (зелений), низька = аномалія (червоний)
                        ("#FF6B6B" if v>4 else "#F5A623" if v>2 else "#00D4AA")
                        if is_agri else
                        ("#00D4AA" if v>=1.5 else "#F5A623" if v>=0.5 else "#FF6B6B")
                        for v in viirs_df["avg_radiance"]
                    ],
                ))
                if is_agri:
                    fig2.add_hline(y=2.0, line_dash="dash", line_color="#FF6B6B",
                                   annotation_text="Поріг аномалії", annotation_font_color="#FF6B6B")
                else:
                    fig2.add_hline(y=1.5, line_dash="dash", line_color="#F5A623",
                                   annotation_text="Мін. норма для забудови", annotation_font_color="#F5A623")
                fig2.update_layout(title="VIIRS · Нічна активність (нВт/см²/ср)",
                                   height=340, showlegend=False, **PLOTLY_DARK)
                st.plotly_chart(fig2, use_container_width=True)
                viirs_legend = (
                    "зелений = норма, жовтий = помірно, червоний = аномалія"
                    if is_agri else
                    "зелений = норма (є активність), жовтий = низька, червоний = занедбана ділянка"
                )
                st.caption(f"Джерело: NASA/NOAA VIIRS DNB via Google Earth Engine · {viirs_legend}")
    else:
        st.markdown("""
        <div style="text-align:center;padding:3rem;background:#0B1425;border:1px dashed #1A2E4A;border-radius:12px;margin-top:1rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">🛰️</div>
            <div style="color:#3D5070;font-size:0.9rem">Завантажте demo кейс або натисніть «Запустити скан»</div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 2 — Price corridor
# ══════════════════════════════════════════════

with tab_price:
    st.markdown("### Ціновий коридор")
    st.caption("Статистичний аналіз завершених аукціонів Прозорро.Продажі")

    m1, m2, m3 = st.columns(3)
    m1.metric("P25 · Мінімум ринку",  f"{min_p:,.0f} грн/рік")
    m2.metric("Медіана · Орієнтир",   f"{median_p:,.0f} грн/рік")
    m3.metric("P85 · Максимум ринку", f"{max_p:,.0f} грн/рік")

    st.divider()
    st.markdown("#### Симуляція аукціону")
    st.caption("Рухайте повзунок — система миттєво показує вердикт")

    slider_max = int(max_p * 1.8) if max_p > 0 else 200_000
    proposed = st.slider(
        "Пропонована ціна:", min_value=0, max_value=slider_max,
        value=int(median_p) if median_p > 0 else slider_max // 2,
        step=1000, format="%d грн", label_visibility="collapsed",
    )

    verdict = price_corridor.price_verdict(proposed, min_p, max_p, median_p)
    if verdict["verdict"] == "suspicious_low":
        st.error(verdict["message"])
        st.markdown(f"**💸 Потенційні втрати:** {(median_p - proposed):,.0f} грн/рік")
    elif verdict["verdict"] == "suspicious_high":
        st.warning(verdict["message"])
    elif verdict["verdict"] == "fair":
        st.success(verdict["message"])

    bar_color = "#FF6B6B" if verdict["verdict"]=="suspicious_low" else "#00D4AA" if verdict["verdict"]=="fair" else "#F5A623"
    fig_bar = go.Figure(go.Bar(
        x=["P25 (мін)", "Медіана", "P85 (макс)", "Пропозиція"],
        y=[min_p, median_p, max_p, proposed],
        marker_color=["#1A2E4A","#00D4AA","#1A2E4A", bar_color],
        text=[f"{v:,.0f}" for v in [min_p, median_p, max_p, proposed]],
        textposition="outside", textfont=dict(color="#B0BDD4", size=11),
    ))
    fig_bar.update_layout(title="Ціновий коридор Прозорро vs пропозиція",
                          yaxis_title="грн/рік", height=320,
                          showlegend=False, **PLOTLY_DARK)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()
    st.markdown("### Порівняльні угоди · Прозорро.Продажі")

    with st.spinner("Завантаження лотів…"):
        if st.session_state.prozorro_df is None:
            from prozorro import fetch_land_lots
            st.session_state.prozorro_df = fetch_land_lots(limit=50)

    df_proz = st.session_state.prozorro_df
    if df_proz is not None and len(df_proz) > 0:
        show_cols = ["title","area_ha","price_per_ha","region","date"]
        available = [c for c in show_cols if c in df_proz.columns]
        display_df = df_proz[available].head(10).copy()
        display_df.columns = [{"title":"Назва лоту","area_ha":"Площа (га)",
            "price_per_ha":"Ціна/га/рік (грн)","region":"Регіон","date":"Дата"}.get(c,c)
            for c in available]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        st.caption(f"Показано {len(display_df)} з {len(df_proz)} завершених аукціонів")
    else:
        st.info("Дані Прозорро завантажуються або недоступні")


# ══════════════════════════════════════════════
# TAB 3 — Budget
# ══════════════════════════════════════════════

with tab_budget:
    st.markdown("### Розподіл бюджету громади")
    st.caption("LP-модель (PuLP / CBC solver) розподіляє дохід від монетизації активу")

    budget_input = st.number_input(
        "Вивільнений річний дохід (грн):",
        min_value=0, value=int(median_p) if median_p > 0 else 100_000, step=10_000,
    )
    result = budget_optimizer.optimize_budget(total_funds=budget_input)
    st.session_state.budget_result = result

    b1, b2, b3 = st.columns(3)
    b1.metric("Школи",    f"{result['Школи (грн)']:,.0f} грн")
    b2.metric("Дороги",   f"{result['Дороги (грн)']:,.0f} грн")
    b3.metric("Медицина", f"{result['Медицина (грн)']:,.0f} грн")

    fig_pie = px.pie(
        names=["Школи","Дороги","Медицина"],
        values=[result["Школи (грн)"], result["Дороги (грн)"], result["Медицина (грн)"]],
        color_discrete_sequence=["#00D4AA","#3B82F6","#F5A623"],
        hole=0.45,
    )
    fig_pie.update_traces(
        textfont_color="#E8EDF5",
        textfont_family="Space Grotesk",
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} грн<br>%{percent}<extra></extra>",
    )
    fig_pie.update_layout(
        title="Розподіл за соціальною корисністю",
        height=380,
        paper_bgcolor="#080E1C",
        font=dict(family="Space Grotesk", color="#B0BDD4"),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    st.caption(f"Статус солвера: {result.get('Статус','N/A')}")


# ══════════════════════════════════════════════
# TAB 4 — Multi-parcel
# ══════════════════════════════════════════════

with tab_multi:
    st.markdown("### Аналіз кількох ділянок")

    with st.expander("Інструкція", expanded=True):
        st.markdown("""
**Ідея:** замість аналізувати одну ділянку вручну — завантажте список ділянок
і система проаналізує всі одразу та видасть рейтинг за потенціалом монетизації.

**Крок 1 — Завантажте шаблон** ⬇️

Натисніть кнопку нижче. Отримаєте CSV файл з колонками:
`name` · `lat` · `lon` · `area_ha` · `land_type`

**Крок 2 — Заповніть своїми даними** ✏️

Відкрийте у **Google Sheets** (перетягніть — кодування збережеться автоматично).
Координати: Google Maps → правий клік → скопіюйте два числа.

Допустимі `land_type`: `Сільське господарство` · `Пасовище` · `Забудова` · `Промисловість`

**Крок 3 — Завантажте назад і отримайте рейтинг** 🏆

Система запускає супутниковий скан для кожної ділянки і будує таблицю за Asset Score.
        """)

    st.divider()

    template = pd.DataFrame({
        "name": ["Ділянка 1","Ділянка 2","Ділянка 3"],
        "lat": [49.444,49.588,49.233], "lon": [31.998,34.551,28.468],
        "area_ha": [8.5,12.0,5.0],
        "land_type": ["Сільське господарство","Пасовище","Забудова"],
    })
    st.download_button("Завантажити шаблон CSV",
        data=template.to_csv(index=False, encoding="utf-8-sig"),
        file_name="terraaudit_parcels_template.csv", mime="text/csv")

    uploaded = st.file_uploader("Завантажте CSV з ділянками", type="csv")

    if uploaded:
        try:
            parcels = pd.read_csv(uploaded)
            st.success(f"✅ Завантажено {len(parcels)} ділянок")
            st.dataframe(parcels.head(), use_container_width=True, hide_index=True)

            if st.button("Проаналізувати всі ділянки", type="primary"):
                results = []
                progress = st.progress(0, text="Аналіз ділянок…")
                for i, row in parcels.iterrows():
                    progress.progress((i+1)/len(parcels), text=f"Аналіз: {row.get('name',f'Ділянка {i+1}')}")
                    sat = geoai_engine.analyze_satellite_data(float(row["lat"]), float(row["lon"]), year=start_year)
                    score = analysis.calculate_asset_score(
                        sat["ndvi_score"], sat["ndbi_score"], sat["night_light_rad"],
                        sat["sar_detected_changes"], str(row.get("land_type","Сільське господарство")),
                        float(row.get("area_ha",5.0)),
                    )
                    _, _, med = price_corridor.calculate_corridor(
                        float(row.get("area_ha",5.0)), str(row.get("land_type","Сільське господарство")))
                    results.append({
                        "Назва": row.get("name",f"Ділянка {i+1}"),
                        "Asset Score": score.score, "Рівень": f"{score.emoji} {score.label}",
                        "NDVI": round(sat["ndvi_score"],3), "VIIRS": round(sat["night_light_rad"],2),
                        "SAR": "✅" if sat["sar_detected_changes"] else "—",
                        "Медіана (грн/р)": f"{med:,.0f}",
                    })
                progress.empty()
                results_df = pd.DataFrame(results).sort_values("Asset Score", ascending=False)

                st.markdown("#### Рейтинг ділянок")
                st.dataframe(
                    results_df.style.map(
                        lambda v: ("background-color:#2D1515;color:#FF6B6B" if v>=7
                                   else "background-color:#2A1F0A;color:#F5A623" if v>=4
                                   else "background-color:#0D2519;color:#00D4AA"),
                        subset=["Asset Score"]
                    ),
                    use_container_width=True, hide_index=True,
                )
                st.download_button("Завантажити результати CSV",
                    data=results_df.to_csv(index=False, encoding="utf-8-sig"),
                    file_name="terraaudit_results.csv", mime="text/csv")

                fig_rank = px.bar(results_df, x="Назва", y="Asset Score",
                    color="Asset Score", color_continuous_scale=["#00D4AA","#F5A623","#FF6B6B"],
                    title="Рейтинг за Asset Score", range_color=[0,10])
                fig_rank.update_layout(height=320, showlegend=False, **PLOTLY_DARK)
                st.plotly_chart(fig_rank, use_container_width=True)

        except Exception as e:
            st.error(f"Помилка читання CSV: {e}")
    else:
        st.markdown("#### Demo кейси")
        demo_results = []
        for name, case in analysis.DEMO_CASES.items():
            sat = case["sat_data"]
            sc = analysis.calculate_asset_score(
                sat["ndvi_score"], sat["ndbi_score"], sat["night_light_rad"],
                sat["sar_detected_changes"], case["land_type"], case["area_ha"],
            )
            demo_results.append({
                "Кейс": name, "Asset Score": sc.score,
                "Рівень": f"{sc.emoji} {sc.label}",
                "NDVI": sat["ndvi_score"], "VIIRS": sat["night_light_rad"],
            })
        st.dataframe(
            pd.DataFrame(demo_results).style.map(
                lambda v: ("background-color:#2D1515;color:#FF6B6B" if v>=7
                           else "background-color:#2A1F0A;color:#F5A623" if v>=4
                           else "background-color:#0D2519;color:#00D4AA"),
                subset=["Asset Score"]
            ),
            use_container_width=True, hide_index=True,
        )


# ══════════════════════════════════════════════
# TAB 5 — Report & Teaser
# ══════════════════════════════════════════════

with tab_report:
    st.markdown("### Звіт та Інвестиційний тізер")

    r1, r2 = st.columns(2)

    with r1:
        st.markdown("#### Інвестиційний тізер")
        if not groq_ok:
            st.warning("Додайте GROQ_API_KEY у .env")
        else:
            if st.button("Згенерувати тізер", type="primary", use_container_width=True):
                sat = st.session_state.sat_data
                with st.spinner("Groq генерує тізер…"):
                    teaser = llm_teaser.generate_teaser(
                        community_name=st.session_state.address,
                        area=st.session_state.area_ha,
                        land_type=st.session_state.land_type,
                        market_price=st.session_state.median_p,
                        ndvi_score=sat["ndvi_score"] if sat else None,
                        viirs_rad=sat["night_light_rad"] if sat else None,
                        sar_changed=sat["sar_detected_changes"] if sat else False,
                    )
                st.session_state.teaser_text = teaser
            if st.session_state.teaser_text:
                st.markdown(st.session_state.teaser_text)
                st.download_button("Завантажити тізер (.md)",
                    data=st.session_state.teaser_text,
                    file_name="terraaudit_teaser.md", mime="text/markdown")

    with r2:
        st.markdown("#### PDF звіт")
        st.caption("Asset Score · порівняльна таблиця · ціновий коридор · бюджет · тізер")

        can_pdf = (st.session_state.scan_done
                   and st.session_state.sat_data is not None
                   and st.session_state.asset_score is not None)

        if not can_pdf:
            st.markdown("""
            <div style="padding:1.5rem;background:#0B1425;border:1px dashed #1A2E4A;border-radius:10px;text-align:center">
                <div style="color:#3D5070;font-size:0.85rem">👆 Спочатку завантажте demo кейс або проведіть скан</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.button("Згенерувати PDF", type="primary", use_container_width=True):
                with st.spinner("Генерація PDF…"):
                    try:
                        pdf_bytes = report.generate_pdf(
                            address=st.session_state.address,
                            area_ha=st.session_state.area_ha,
                            land_type=st.session_state.land_type,
                            sat_data=st.session_state.sat_data,
                            asset_score=st.session_state.asset_score,
                            comparison_df=st.session_state.comparison_df,
                            min_p=st.session_state.min_p,
                            median_p=st.session_state.median_p,
                            max_p=st.session_state.max_p,
                            budget_result=st.session_state.budget_result,
                            teaser_text=st.session_state.teaser_text,
                            prozorro_df=st.session_state.prozorro_df,
                        )
                        st.download_button("Завантажити PDF звіт",
                            data=pdf_bytes, file_name="TerraAudit_Report.pdf",
                            mime="application/pdf", type="primary",
                            use_container_width=True)
                        st.success("✅ PDF готовий!")
                    except Exception as e:
                        st.error(f"Помилка генерації PDF: {e}")

            if st.session_state.asset_score:
                sc = st.session_state.asset_score
                st.divider()
                st.caption("Звіт містить:")
                items = [
                    f"Asset Score: {sc.score}/10 ({sc.label})",
                    "Супутникові дані: NDVI, NDBI, VIIRS, SAR",
                    "Ціновий коридор Прозорро",
                    "Порівняльна таблиця кадастр vs супутник",
                    "Бюджет громади (LP-оптимізація)",
                    "Інвестиційний тізер" if st.session_state.teaser_text else "Тізер: не згенеровано",
                ]
                for item in items:
                    st.markdown(f"<div style='font-size:0.82rem;color:#6B7FA3;padding:0.15rem 0'>· {item}</div>", unsafe_allow_html=True)