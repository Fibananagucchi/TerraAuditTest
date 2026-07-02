# TerraAudit

**Satellite Asset Intelligence for Ukrainian Communities**

TerraAudit is an AI-powered land asset auditing system that helps Ukrainian municipalities discover and monetize underutilized land. It combines satellite imagery from ESA Sentinel-2, NASA/NOAA VIIRS, and ESA Sentinel-1 SAR (via Google Earth Engine) with open auction data from Prozorro.Sale to identify assets, assess their market value, and generate investment proposals.

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

## Quick Start (no authorization required)

To explore the system without GEE setup:

1. Install dependencies — `pip install -r requirements.txt`
2. Run `streamlit run app.py` — no `.env` file needed
3. In the sidebar, select one of the preloaded cases under **"Quick Start"**
4. Click **"Load Case"** — the system will display synthetic demo data with full UI

---

## Requirements

- Python 3.10+
- Google Cloud project with Earth Engine API enabled
- Account registered at [earthengine.google.com](https://earthengine.google.com)
- (Optional) Groq API key for AI teaser generation

---

*Built at Noosphere Engineering School Hackathon · Theme: City of the Future*
