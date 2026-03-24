# Ticketmastery Dashboard

A CSV-driven frontend map prototype and exploratory analytics suite for maintenance ticket analysis. The project consists of a standalone browser dashboard and a companion Streamlit map application.

---

## Project Structure

```
/
├── index.html               # Dashboard entry point
├── styles.css               # Dashboard styles and theme variables
├── app.js                   # Dashboard logic and panel rendering
├── README.md                # This file
└── map_code/
    ├── map_app.py           # Streamlit + PyDeck interactive map application
    └── ticket_heat_map.ipynb  # Jupyter notebook version of the map app
```

---

## Components

### Browser Dashboard (`index.html` / `app.js` / `styles.css`)

A fully client-side HTML/CSS/JS dashboard — no build step or server required. Load it directly in a browser. Upload one or two CSV files and all six analysis panels render instantly.

**Six analysis panels:**

| Panel | Description |
|-------|-------------|
| 1. Repetitive Assets | Identifies assets with multiple tickets within a configurable X-day window |
| 2. Corrective Ticket Heat Map | Day-of-week breakdown of corrective tickets by building |
| 3. Preventative vs. Non-Preventative | Compares corrective ticket rates and survey scores for assets with/without PM |
| 4. Keyword Search + Word Cloud | Filters ticket descriptions by keyword; renders a frequency word cloud |
| 5. Asset ID Data Sparsity | Shows the proportion of tickets missing an Asset ID, broken down by building |
| 6. Outlier Detection (Preview) | Z-score heuristic ranking tickets by description length, survey score, and missing asset penalty |

**Expected CSV columns:**

| Column | Source | Notes |
|--------|--------|-------|
| `WORK_TASK_ID` | Assets CSV | Primary ticket identifier |
| `DESCRIPTION` | Assets CSV | Free-text work description |
| `TASK_TYPE` | Assets CSV | e.g. `Corrective`, `Preventative` |
| `TASK_PRIORITY` | Assets CSV | Ticket priority level |
| `ASSET_ID` | Assets CSV | Asset identifier |
| `ASSET_NAME` | Assets CSV | Human-readable asset name |
| `ASSET_PRIMARY_LOCATION_BUILDING` | Assets CSV | Building grouping |
| `CREATE_DATE_LTZ` | Assets CSV | Ticket creation timestamp |
| `average_survey_score` | Surveys CSV | Optional; 0–5 satisfaction score |
| `building` | Surveys CSV | Optional; overridden by asset building if both present |
| `BASELINE_START_LTZ` | Surveys CSV | Optional; used as event date when present |

Two CSV files can be uploaded and are joined on `WORK_TASK_ID`. Sample data is pre-loaded so the dashboard works immediately on open.

---

### Interactive Map (`map_code/map_app.py`)

A Streamlit application rendering a 3D column-layer map of ticket density by building using PyDeck. Requires a CSV with building coordinates (`FEP_BUILDING_X_COORDINATE`, `FEP_BUILDING_Y_COORDINATE`).

**Features:**
- Date range slider filtering
- Keyword search on ticket descriptions
- Multi-select filters for Service Class, Building Class, Task Type, and Priority
- Dynamic column heights and color bins (blue → green → yellow → orange → red) scaled to ticket count
- Tooltip showing building name, class, and ticket count
- CSV export of the filtered dataset
- Map centered on the University of Houston campus (configurable via `view_state`)

**Prerequisites:**
```bash
pip install streamlit pandas pydeck
```

**Run:**
```bash
streamlit run map_code/map_app.py
```

---

### Jupyter Notebook (`map_code/ticket_heat_map.ipynb`)

A cell-by-cell version of `map_app.py` for exploratory use in Jupyter. Contains the same logic broken into four cells: imports, data loading, Streamlit UI/filters, and PyDeck rendering.

**Prerequisites:**
```bash
pip install jupyter pandas pydeck streamlit
```

> The notebook is intended for development and iteration; run `map_app.py` with Streamlit for the interactive application.

---

## Quick Start

### Dashboard
1. Open `index.html` in any modern browser — no installation needed.
2. Optionally upload `merged_tickets_assets.csv` and/or `merged_tickets_assets_surveys.csv` using the file inputs in the header.
3. Adjust the X-day window and use the Keyword Search panel to explore the data.

### Map Application
1. Install dependencies: `pip install streamlit pandas pydeck`
2. Update the CSV path in `map_app.py` (line: `raw = load_data(r'...')`)
3. Run: `streamlit run map_code/map_app.py`