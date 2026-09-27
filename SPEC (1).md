# SPEC.md
# AI-Based Tropical Cyclone Intelligence & GIS Decision-Support System
# SIH 2026 – Problem Statement 26083

## 1. PROJECT OBJECTIVE

Build a real, functional AI/ML-based tropical cyclone intelligence and GIS decision-support system using real satellite and environmental data.

The product must connect:

OBSERVE → UNDERSTAND → PREDICT → LOCATE → ASSESS → SIMULATE → ALERT

It must support three clearly separated modes:

1. LIVE MONITORING — latest available real satellite observation and live/near-real-time inference.
2. HISTORICAL REPLAY — real historical satellite/best-track data for reproducible analysis and model validation.
3. SIMULATION — scenario analysis that changes the modeled track/risk corridor and recalculates geographic exposure.

The system is a decision-support prototype, not an official government warning system.

## 2. REAL DATA REQUIREMENT — NON-NEGOTIABLE

Do NOT build a fake/demo dashboard that only uses hard-coded JSON, random values, placeholder charts, generated satellite images, or invented live status.

Where an external source is available, the application must retrieve real data through a proper backend/provider layer.

Every live observation must show:
- source
- observation timestamp
- retrieval/update status
- LIVE indicator

If live data is unavailable, clearly show:
LIVE DATA UNAVAILABLE
and allow HISTORICAL REPLAY.

Never silently substitute historical or simulated data while displaying LIVE.

## 3. DATA SOURCES

### Historical training/reference
- HURSAT-B1: https://www.ncei.noaa.gov/products/hurricane-satellite-data
- HURSAT-AVHRR: historical satellite observations
- IBTrACS: https://www.ncei.noaa.gov/products/international-best-track-archive
- ERA5: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels

### Live/near-real-time Indian satellite
- MOSDAC / ISRO: https://mosdac.gov.in/
- MOSDAC cyclone services: https://mosdac.gov.in/cyclone

The implementation must verify the currently available MOSDAC/ISRO product/API/download mechanism before coding the live provider. Do not invent an API endpoint.

### GIS/exposure
- WorldPop: https://www.worldpop.org/datacatalog
- Geofabrik/OpenStreetMap: https://download.geofabrik.de/asia/india.html
- District boundaries: https://nwdp.nwic.gov.in/dataset/district-boundary

## 4. OPERATING MODES

### LIVE MONITORING

Flow:

LIVE INSAT/MOSDAC OBSERVATION
→ VALIDATION
→ PREPROCESSING
→ AI INFERENCE
→ CYCLONE ANALYSIS
→ TRACK PREDICTION
→ GIS EXPOSURE
→ DECISION SUPPORT

Show:
LIVE
INSAT/MOSDAC
actual timestamp

The UI should update when new source data becomes available. Do not use a fake continuously changing animation to imply live updates.

### HISTORICAL REPLAY

Allow selection of a real historical cyclone and replay observations chronologically.

Show:
HISTORICAL REPLAY
storm name/ID
date/time
source

Allow comparison of predicted vs observed historical track where the model has been evaluated.

### SIMULATION

Allow:
- track shift
- risk corridor width
- supported intensity scenario

Show:
SIMULATION
NOT AN OFFICIAL FORECAST

Recalculate GIS exposure from the changed scenario.

## 5. DATA PROVIDER ARCHITECTURE

Use provider abstraction so live and historical sources can change independently.

Providers:
- HistoricalHursatProvider
- IbtracsProvider
- Era5Provider
- LiveInsatProvider
- PopulationProvider
- InfrastructureProvider

Common concepts:
getLatestObservation()
getHistoricalObservation()
getStormTrack()
getEnvironmentalData()
getSourceMetadata()
getProviderStatus()

The frontend must never directly contain provider credentials or secret keys.

## 6. AI ENGINE

Modules:

### Detection
Detect cyclone activity from satellite observation/sequence.

### Pattern/stage classification
Use labels supported by the training/reference data.

### Evolution analysis
Analyze temporal changes such as organization, symmetry, central structure and modeled intensity trend.

Possible output:
- Developing
- Strengthening
- Stable
- Weakening
- Reorganizing

Only display model outputs that have actually been trained and validated.

### Track prediction
Initial model may use LSTM/GRU sequence architecture.

Inputs may include:
- historical positions
- satellite-derived features
- temporal features
- selected environmental variables

Output:
future latitude/longitude for horizons actually supported by validation.

### Intensity trend
Minimum useful output:
- Strengthening
- Stable
- Weakening

Exact future wind speed/pressure must NOT be displayed unless a separately trained and validated model exists.

## 7. TRAINING AND VALIDATION

Historical data trains/validates the AI.

Avoid leakage between storms in train/test splits where feasible.

Metrics may include:
- MAE
- RMSE
- mean track distance error
- classification metrics

Never hard-code accuracy claims. Dashboard metrics must come from actual experiment results.

## 8. GIS INTELLIGENCE

Predicted track
→ modeled risk corridor
→ spatial intersection
→ districts
→ estimated population
→ infrastructure

Map layers:
- current/observed cyclone position
- observed historical track
- predicted track
- modeled risk corridor
- district boundaries
- population
- roads
- hospitals
- ports
- airports
- other critical infrastructure where available

Use wording:
"Modeled risk corridor"
"Estimated population within modeled zone"

Do not claim actual damage or actual affected population without a validated impact model.

## 9. IMPACT SHIFT SIMULATOR

This is a core differentiator.

Base scenario:
- modeled track
- modeled corridor
- exposure

Scenario:
- shifted track
- changed corridor width
- supported intensity scenario

Recalculate:
- districts
- estimated population
- infrastructure

Show side-by-side:
BASE SCENARIO
SIMULATED SCENARIO

This is scenario analysis, not an official forecast.

## 10. DECISION-SUPPORT ALERT

Generate a clear authority-facing summary:

Storm
Mode
Source
Observation time
Current status
Evolution
Movement
Modeled risk
Districts in modeled corridor
Estimated population
Infrastructure exposure

Label it:
AI DECISION-SUPPORT ALERT

Never call it an official warning.

## 11. DASHBOARD

Primary authority dashboard:

1. Mode selector: LIVE / HISTORICAL / SIMULATION
2. Data source and timestamp
3. Cyclone status
4. Satellite observation
5. Evolution timeline/fingerprint
6. Track prediction
7. Intensity trend if available
8. GIS map
9. Modeled risk corridor
10. District exposure
11. Population exposure
12. Infrastructure exposure
13. Explainability/evidence
14. Impact Shift Simulator
15. Decision-support alert

## 12. UI/UX — IMPORTANT

The product must look like a real professional scientific/disaster-management application, NOT like an AI-generated template.

Avoid:
- black backgrounds
- dark blue full-page backgrounds
- neon gradients
- excessive glowing effects
- futuristic AI decorations
- unnecessary glassmorphism
- giant meaningless numbers
- fake satellite animations
- generic "AI dashboard" styling
- excessive rounded cards
- decorative elements with no function

Preferred visual direction:
- clean white/light-gray base
- restrained professional accent colors
- readable dark text
- subtle borders and shadows
- strong information hierarchy
- real map as the visual centerpiece
- compact cards only where useful
- typography-first layout
- generous whitespace
- scientific/institutional feel
- simple navigation

Suggested palette:
- white / warm off-white
- very light gray surfaces
- charcoal text
- muted red/orange only for warnings
- muted green for safe/normal states
- restrained neutral accent for interactive elements

Do NOT force a blue theme.

The UI should look designed by a professional product designer, not generated by an AI dashboard generator.

## 13. REAL-TIME UX

For LIVE mode:
- show actual source timestamp
- show "last updated" time
- show provider connection status
- show loading state while retrieving data
- show "data unavailable" when the source fails
- refresh only according to the source/provider's actual update availability
- do not fake real-time movement

When new data arrives:
- update observation
- rerun inference if appropriate
- update prediction
- update GIS exposure
- update alert summary
- retain previous observation for comparison

## 14. SOURCE TRANSPARENCY

Every major visualization must expose its source.

Examples:

LIVE | INSAT/MOSDAC | 09:30 UTC
HISTORICAL REPLAY | HURSAT-B1 | 2012-10-28 06:00 UTC
REFERENCE | IBTrACS
ENVIRONMENT | ERA5
SIMULATION | USER SCENARIO

Include a small "Data & Method" panel explaining:
- source
- timestamp
- model version
- whether the result is live, historical, or simulated
- known limitations

## 15. ERROR AND FALLBACK BEHAVIOR

If provider unavailable:
LIVE DATA UNAVAILABLE

If model unavailable:
MODEL UNAVAILABLE

If data is stale:
STALE DATA — LAST OBSERVATION [timestamp]

If a feature is not validated:
NOT AVAILABLE

Never replace missing live data with random or invented values.

## 16. TECH STACK

Frontend:
- React / Next.js
- TypeScript
- Tailwind CSS

Mapping:
- MapLibre or Leaflet

Charts:
- Recharts/ECharts

Backend:
- Python
- FastAPI

ML:
- PyTorch
- scikit-learn
- NumPy
- pandas

Scientific:
- xarray
- NetCDF tools

GIS:
- GeoPandas
- Shapely
- Rasterio
- PyProj

Database:
- PostgreSQL + PostGIS

## 17. API

Data:
GET /api/data/live/latest
GET /api/data/historical/storms
GET /api/data/historical/storm/{id}
GET /api/data/source-status

AI:
POST /api/ai/detect
POST /api/ai/classify
POST /api/ai/evolution
POST /api/ai/track
POST /api/ai/intensity-trend
POST /api/ai/analyze

GIS:
POST /api/gis/risk-corridor
POST /api/gis/exposure

Simulation:
POST /api/simulation/run

Alerts:
POST /api/alerts/generate
POST /api/alerts/email

## 18. DATA DIRECTORY

data/
├── raw/
│   ├── hursat_b1/
│   ├── hursat_avhrr/
│   ├── ibtracs/
│   ├── era5/
│   ├── insat/
│   └── gis/
├── processed/
│   ├── satellite/
│   ├── sequences/
│   ├── tracks/
│   ├── intensity/
│   └── gis/
├── models/
│   ├── detection/
│   ├── classification/
│   ├── evolution/
│   ├── track/
│   └── intensity/
└── metadata/

## 19. MODEL VERSIONING

Every prediction stores:
- model version
- source
- timestamp
- operating mode
- prediction horizon
- generated_at
- output geometry
- validation status

Example:
Track-LSTM-v1 | INSAT/MOSDAC | LIVE

## 20. DEMO

Historical:
real storm → satellite sequence → AI analysis → prediction → observed-vs-predicted → GIS exposure → simulator → alert.

Live:
real INSAT/MOSDAC observation → source timestamp → AI inference → prediction → GIS exposure.

If live source is unavailable:
clearly show unavailable status and switch to historical replay.

Never fake live data.

## 21. IMPLEMENTATION ORDER

Build in this order:

1. Clean UI shell
2. Real historical data provider
3. Historical replay
4. GIS map and layers
5. Baseline AI model
6. Track prediction
7. Exposure analysis
8. Impact Shift Simulator
9. Live provider integration
10. Live inference
11. Decision-support alerts
12. Testing and source transparency

Do not spend most development time on visual effects before the data pipeline works.

## 22. QUALITY BAR

The finished system should feel like a real prototype built by a capable engineering/product team.

It must be:
- functional
- reproducible
- source-transparent
- scientifically cautious
- visually simple
- responsive
- maintainable
- extensible

The demo must work even if a live provider temporarily fails, but it must never pretend the fallback is live.

## 23. FINAL PRODUCT STORY

OBSERVE
→ AI UNDERSTANDS
→ EVOLUTION IS TRACKED
→ FUTURE MOVEMENT IS PREDICTED
→ GIS LOCATES MODELED RISK
→ EXPOSURE IS CALCULATED
→ SCENARIOS ARE SIMULATED
→ DECISION-SUPPORT INFORMATION IS GENERATED

One-line description:

"An AI-powered multi-source satellite cyclone intelligence and GIS decision-support system that observes cyclone evolution, predicts future movement, maps modeled geographic exposure, and enables scenario-based impact analysis."
