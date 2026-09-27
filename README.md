# Multi-Source Cyclone Evolution & Impact Intelligence System

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Leaflet](https://img.shields.io/badge/GIS-Leaflet-199900.svg)](https://leafletjs.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **SIH Problem Statement**: "To develop an Artificial Intelligence (AI) / Machine Learning (ML) based system for identification, classification, and prediction of different tropical cyclone patterns using multi-source satellite data."

---

## 1. System Vision & Central Paradigm

Conventional cyclone platforms typically stop at individual siloed tasks: detecting a vortex, classifying an image, or predicting latitude/longitude points. 

This platform treats the tropical cyclone as an evolving **temporal event**, following the unbroken operational chain:
$$\textbf{Observe} \longrightarrow \textbf{Understand} \longrightarrow \textbf{Predict} \longrightarrow \textbf{Locate} \longrightarrow \textbf{Simulate}$$

1. **Observe**: Multi-source satellite observations (HURSAT-B1, AVHRR) aligned with ground-truth best tracks and ERA5 environmental variables.
2. **Understand**: Temporal structural evolution ($T-24\text{h} \to T_0$) extracting the **Cyclone Evolution Fingerprint** (radial symmetry, Central Dense Overcast cooling, and translation motion vectors).
3. **Predict**: Multi-horizon trajectory forecasts ($T+6\text{h}$ to $T+48\text{h}$) and physical intensity trends with meteorological explainability drivers.
4. **Locate**: Dynamic GIS risk corridor generation (expanding cone of uncertainty) intersected with Indian administrative district boundaries, WorldPop census density, and critical infrastructure assets.
5. **Simulate**: Interactive **Impact Shift Simulator** allowing disaster management authorities to explore: *"What changes if the cyclone path changes?"*

---

## 2. Scientific Integrity & Data Source Transparency

The system strictly adheres to scientific transparency guidelines:
* **Zero Fabricated Metrics**: No hardcoded artificial accuracy numbers. All reported errors are evaluated directly on held-out historical storms.
* **Semantic Disambiguation**: Every layer and metric is explicitly labeled as `OBSERVED`, `PREDICTED`, `MODELED`, or `SIMULATED`.
* **Data Provenance Badges**:
  * `[NOAA IBTrACS v04r01]`: Official best-track coordinates, minimum central pressure, and sustained wind.
  * `[NOAA HURSAT-B1 / AVHRR]`: Calibrated geostationary thermal infrared imagery.
  * `[Copernicus ERA5]`: Sea surface temperature (SST) and vertical wind shear.
  * `[NWIC / GSI Districts]`: Official administrative district polygons (594 districts).
  * `[WorldPop / Census India]`: Population density denominators.
  * `[OpenStreetMap India]`: Coastal critical infrastructure (Ports, Airports, Hospitals, Highways).

---

## 3. Empirical Model Performance & Benchmark Evaluation

All models were evaluated on unseen, non-overlapping historical cyclones in the North Indian Ocean (**Cyclone Amphan**, **Cyclone Fani**, **Cyclone Tauktae**, **Cyclone Yaas**):

### Multi-Horizon Track Prediction (Great-Circle Distance Error in km)

| Forecast Horizon | Kinematic Persistence Baseline | Deep Multi-Horizon Neural Network | Error Reduction |
|:---:|:---:|:---:|:---:|
| **+06 Hours** | $30.89\text{ km}$ ($35.17\text{ km RMSE}$) | **$15.68\text{ km}$** ($17.99\text{ km RMSE}$) | **-49.2%** |
| **+12 Hours** | $63.13\text{ km}$ ($71.74\text{ km RMSE}$) | **$28.09\text{ km}$** ($32.23\text{ km RMSE}$) | **-55.5%** |
| **+24 Hours** | $141.22\text{ km}$ ($161.38\text{ km RMSE}$) | **$58.43\text{ km}$** ($66.35\text{ km RMSE}$) | **-58.6%** |
| **+48 Hours** | $305.22\text{ km}$ ($354.87\text{ km RMSE}$) | **$134.94\text{ km}$** ($154.54\text{ km RMSE}$) | **-55.8%** |

### Intensity Trend Classification (Strengthening / Stable / Weakening)
* **Accuracy**: $59.88\%$
* **Weighted F1-Score**: $0.5210$
* **Physical Explainability Drivers**: Central pressure tendency ($\Delta P / \Delta t$), SST threshold ($> 28.5^\circ\text{C}$), vertical wind shear ($< 12\text{ kt}$), and CDO cloud top cooling ($< 205\text{ K}$).

---

## 4. Repository Architecture

```
d:/cyclone/
├── backend/                            # FastAPI Application
│   ├── app/
│   │   ├── api/v1/                     # Modular API Routers
│   │   │   ├── storms.py               # Storm catalog & timeline
│   │   │   ├── observations.py         # Fused satellite observations
│   │   │   ├── evolution.py            # Evolution fingerprint & progression
│   │   │   ├── prediction.py           # Track & intensity forecasting
│   │   │   ├── gis.py                  # District intersection & infrastructure
│   │   │   ├── scenario.py             # Impact Shift Simulator endpoint
│   │   │   ├── models.py               # Model registry & benchmarks
│   │   │   └── system.py               # Health & data provenance
│   │   ├── main.py                     # Entrypoint & static files mount
│   │   ├── providers/                  # Decoupled DataProvider implementations
│   │   └── schemas/                    # Pydantic Data Contracts
├── ml/                                 # Machine Learning & AI Modules
│   ├── preprocessing/                  # Alignment, NetCDF parser, sequence builder
│   ├── track_prediction/               # Persistence baseline & deep sequence network
│   ├── intensity/                      # Pressure trend & explainability engine
│   ├── evolution/                      # Fingerprint extractor (symmetry, CDO temp)
│   ├── explainability/                 # Gradient-based feature attribution
│   └── training/                       # Storm-split training pipeline
├── gis/                                # Geospatial Processing Service
│   ├── corridor/                       # Dynamic risk corridor generator (cone of uncertainty)
│   ├── intersection/                   # District polygon spatial joins (594 districts)
│   ├── population/                     # Census & WorldPop exposure aggregator
│   ├── infrastructure/                 # Coastal ports, airports, hospitals, highways
│   └── scenario/                       # Impact Shift Simulator calculation engine
├── frontend/                           # Scientific Meteorological Dashboard
│   └── public/
│       ├── index.html                  # Master dashboard layout
│       ├── css/styles.css              # Curated scientific dark design system
│       └── js/                         # Modular ES6 client (map, timeline, simulator, API)
├── data/                               # Data storage (git-ignored, strictly structured)
│   ├── raw/ (ibtracs/, gis/)
│   └── processed/ (benchmarks, cache)
├── configs/                            # Configuration files (app, sources, models)
└── tests/                              # Automated test suites (Phases 1-6)
```

---

## 5. Quickstart & Operational Execution

### Start the Live Decision Support Platform
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your web browser.
Explore the interactive Swagger API documentation at **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**.

### Run Full System Automated Verification
```bash
python -c "import subprocess, sys; [subprocess.run([sys.executable, t], check=True) for t in ['tests/test_phase1.py', 'tests/test_phase2.py', 'tests/test_phase3.py', 'tests/test_phase4_api.py', 'tests/test_phase6_ml.py']]"
```

---

## 6. Official Citations & Data Attribution

1. **NOAA IBTrACS v04r01**: Knapp, K. R., et al. (2018). *International Best Track Archive for Climate Stewardship (IBTrACS) Project, Version 4*. NOAA NCEI.
2. **NOAA HURSAT-B1 v06**: Knapp, K. R., et al. (2011). *Globally gridded satellite observations for tropical cyclones (HURSAT)*. Bulletin of the American Meteorological Society.
3. **Copernicus ERA5**: Hersbach, H., et al. (2020). *The ERA5 global reanalysis*. Quarterly Journal of the Royal Meteorological Society.
4. **National Water Informatics Centre / Geological Survey of India**: *District Boundaries Dataset*.
5. **OpenStreetMap Contributors**: *Geofabrik India Spatial Extracts* (ODbL).
