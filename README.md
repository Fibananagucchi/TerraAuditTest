# TerraAudit

**Satellite Asset Intelligence for Ukrainian Communities**

TerraAudit is an AI-powered land asset auditing system that helps Ukrainian municipalities discover and monetize underutilized land. It combines satellite imagery from ESA Sentinel-2, NASA/NOAA VIIRS, and ESA Sentinel-1 SAR (via Google Earth Engine) with open auction data from Prozorro.Sale to identify assets, assess their market value, and generate investment proposals.

---

## 🚀 Live Demo

**Try it here, Google Earth Engine already authorized:**

👉 **[https://terraaudit.streamlit.app](https://terraaudit.streamlit.app)**

The hosted version runs with **Live GEE** — real satellite data (Sentinel-2, VIIRS, Sentinel-1 SAR) for any location in Ukraine, no authentication needed on your end.

---

## Features

- **GeoAI Module** — NDVI/NDBI time series (2020–2025), VIIRS night activity, SAR surface change detection
- **Asset Score** — unified monetization potential score (0–10) with component breakdown
- **Year Comparison** — side-by-side delta analysis between two selected years
- **Price Corridor** — statistical market range built from real Prozorro.Sale auction data
- **Budget Optimizer** — LP model (PuLP/CBC) allocating freed funds across social priorities
- **Multi-parcel Analysis** — batch CSV upload with ranked Asset Score leaderboard
- **PDF Report** — full downloadable report for investors or Prozorro submission
- **Investment Teaser** — AI-generated (Groq / llama-3.3-70b) property listing draft

---

## Data Sources

| Data | Satellite / Source | Agency |
|---|---|---|
| NDVI, NDBI | Sentinel-2 | ESA |
| Night activity | VIIRS DNB | NASA / NOAA |
| Surface change | Sentinel-1 SAR | ESA |
| Auction prices | Prozorro.Sale API | Ukrainian Gov |
| USD/UAH rate | NBU API | National Bank of Ukraine |
| Geocoding | Nominatim | OpenStreetMap |

All satellite data is processed via **Google Earth Engine** cloud platform.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/terraaudit.git
cd terraaudit
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

```env
GEE_PROJECT=your-google-cloud-project-id
GROQ_API_KEY=your-groq-api-key
```

**Where to get the keys:**
- `GEE_PROJECT` — [console.cloud.google.com](https://console.cloud.google.com) → create a project → enable Earth Engine API
- `GROQ_API_KEY` — [console.groq.com](https://console.groq.com) (free tier available)

### 5. Authenticate Google Earth Engine

```bash
python auth.py
```

A browser will open — sign in with the same Google account registered at [earthengine.google.com](https://earthengine.google.com).

### 6. Run the app

```bash
streamlit run app.py
```

---

## Demo Mode

If Google Earth Engine is not connected, the app automatically switches to **demo mode**:

- A floating yellow warning appears in the bottom-right corner
- All satellite data is synthetic (pre-generated)
- All other modules (Prozorro, NBU, Groq, budget optimizer) use real live data

Demo mode is intended for showcasing the system logic without GEE authorization.

---

## Project Structure

```
terraaudit/
├── app.py                 # Main Streamlit dashboard
├── geoai_engine.py        # GEE module: Sentinel-2, VIIRS, SAR
├── analysis.py            # Asset Score, comparison table, demo cases
├── price_corridor.py      # Price corridor (Prozorro + NBU)
├── prozorro.py            # Prozorro.Sale API client
├── budget_optimizer.py    # LP budget optimizer (PuLP)
├── llm_teaser.py          # Investment teaser generator (Groq)
├── report.py              # PDF generator (fpdf2 + DejaVu font)
├── auth.py                # Google Earth Engine authentication
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
└── README.md
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit + Plotly + Folium |
| GeoAI | Google Earth Engine Python API |
| Satellite data | ESA Copernicus, NASA VIIRS |
| Optimization | PuLP / CBC solver |
| LLM | Groq API (llama-3.3-70b-versatile) |
| PDF | fpdf2 + DejaVuSans (from matplotlib) |
| Geocoding | Nominatim (OpenStreetMap) |

---

## Quick Start

**Easiest option — use the [live demo](#-live-demo) above.** It's already authorized with Live GEE, so you get real satellite data instantly with no setup.

**To run locally without GEE setup** (synthetic demo data only):

1. Install dependencies — `pip install -r requirements.txt`
2. Run `streamlit run app.py` — no `.env` file needed
3. In the sidebar, select one of the preloaded cases under **"Quick Start"**
4. Click **"Load Case"** — the system will display synthetic demo data with full UI

---
 
## Metrics & Criteria Glossary
 
Plain-language explanation of every indicator the system uses.
 
### 1. Satellite Indicators (GeoAI)
 
| Indicator | What it measures | Source | How to read it |
|---|---|---|---|
| **NDVI** (vegetation index) | How green/alive the surface is | ESA Sentinel-2 | Scale −1…+1. For agricultural land, healthy value is ≥0.35. Below 0.2 likely means the land isn't cultivated. |
| **NDBI** (built-up index) | Presence of hard surfaces (asphalt, concrete, roofs) | ESA Sentinel-2 | Above 0.1 indicates hard cover. Anomaly for farmland; normal for built-up land. |
| **VIIRS** (night brightness) | Night lighting intensity — proxy for nighttime activity | NASA / NOAA | Measured in nW/cm²/sr. High values (>2.5) on farmland = anomaly. Low values (<0.5) on built-up land = possible neglect. |
| **SAR delta** (surface change) | Radar backscatter difference between two periods | ESA Sentinel-1 | Measured in dB. Change >3 dB = significant physical change (construction, earthworks). Radar sees through clouds. |
 
*Note: the "normal vs anomaly" logic inverts depending on declared land type — see section 5.*
 
### 2. Asset Score — Monetization Potential Index
 
A single 0–10 score combining all satellite data into one assessment of how much a parcel is a "hidden asset."
 
| Component | Max points | Scoring logic |
|---|---|---|
| NDVI (vegetation) | 3 | Lower NDVI on farmland → more points (stronger neglect signal) |
| NDBI (built-up) | 2 | Hard cover on farmland → points; opposite for built-up land |
| VIIRS (night activity) | 3 | High activity on farmland or low activity on built-up land → points |
| SAR (surface change) | 1 | Surface change on farmland → point |
| Parcel area | 1 | Larger area = higher potential income (linear up to 20 ha) |
 
**Score interpretation:**
 
| Score | Level | Meaning |
|---|---|---|
| 7.0–10.0 | Critical | Strong signs of misuse — audit priority |
| 5.0–6.9 | High | Significant untapped potential — recommend listing on Prozorro |
| 3.0–4.9 | Medium | Moderate potential — needs further verification |
| 0.0–2.9 | Low | Land is used as intended — no anomalies detected |
 
### 3. Price Corridor
 
Statistical fair-rent range built from real completed Prozorro.Sale auctions of the same land type.
 
| Metric | Meaning |
|---|---|
| **P25** (25th percentile) | Lower bound — "market minimum." 25% of real deals were cheaper |
| **Median** | Fair reference price — middle of the sample |
| **P85** (85th percentile) | Upper bound — "market maximum." Only 15% of deals were pricier |
 
**Data confidence levels:**
 
| Badge | Meaning |
|---|---|
| 🎯 Regional data | 5+ real lots of the same type found in the same region with similar area |
| 🌍 National data | Not enough regional lots — used nationwide statistics for this land type |
| 📊 Baseline estimates | Prozorro API temporarily unavailable — used market baseline (USD/ha × official NBU rate) |
 
**Auction simulator verdict:** a price is flagged as suspiciously low if it's below P25 **or** deviates more than −50% from the median (even if technically above P25, which can happen with a wide/skewed sample). Symmetrically, suspiciously high = above P85×1.3 **or** more than double the median.
 
### 4. Budget Optimizer
 
LP model (PuLP/CBC solver) distributing freed-up income across social categories to maximize total "social utility."
 
| Category | Utility weight | Min share | Max share |
|---|---|---|---|
| Medicine | 1.5 | 15% | 50% |
| Schools | 1.2 | 15% | 50% |
| Roads | 1.0 | 10% | 40% |
 
*Utility weight is a relative priority coefficient during optimization (higher = system favors that category within allowed shares). Min/max shares prevent any category from getting 0% or monopolizing the whole budget.*
 
### 5. "Normal vs Anomaly" Logic by Land Type
 
The same satellite value means the opposite depending on the declared land type.
 
| Indicator | Agricultural / Pasture | Built-up / Industrial |
|---|---|---|
| Low NDVI | 🚨 Anomaly (uncultivated) | ✅ Normal (no vegetation expected) |
| High NDBI | 🚨 Anomaly (hard cover) | ✅ Normal (buildings present) |
| High night activity | 🚨 Anomaly (hidden activity) | ✅ Normal (lighting present) |
| Surface change (SAR) | ⚠️ Suspicious (earthworks) | ✅ Normal (construction/repair) |
 
*All thresholds are based on commonly accepted remote-sensing ranges (NDVI/NDBI) and are indicative — intended for initial screening, not as final legal evidence.*
 
---

## Requirements

- Python 3.10+
- Google Cloud project with Earth Engine API enabled
- Account registered at [earthengine.google.com](https://earthengine.google.com)
- (Optional) Groq API key for AI teaser generation

---

*Built at Noosphere Engineering School Hackathon · Theme: City of the Future*