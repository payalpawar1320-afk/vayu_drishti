from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import sys

# Ensure project root in python path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load .env configuration into environment
env_file = BASE_DIR / ".env"
if env_file.exists():
    import os
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.strip().split("=", 1)
                os.environ[k.strip()] = v.strip()

from backend.app.api.v1 import (
    storms, observations, evolution, prediction, gis, scenario, models, system, auth
)

app = FastAPI(
    title="Multi-Source Cyclone Evolution & Impact Intelligence System",
    description="Operational AI & GIS Platform for Tropical Cyclone Observation, Evolution Analysis, Prediction, Geographic Exposure, and Impact Shift Simulation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware for modern frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all local dev origins (Next.js, Vite, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles

# Register API v1 routers
API_V1_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(storms.router, prefix=API_V1_PREFIX)
app.include_router(observations.router, prefix=API_V1_PREFIX)
app.include_router(evolution.router, prefix=API_V1_PREFIX)
app.include_router(prediction.router, prefix=API_V1_PREFIX)
app.include_router(gis.router, prefix=API_V1_PREFIX)
app.include_router(scenario.router, prefix=API_V1_PREFIX)
app.include_router(models.router, prefix=API_V1_PREFIX)
app.include_router(system.router, prefix=API_V1_PREFIX)

@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "vayu-drishti",
        "mode": "operational"
    }

@app.get("/api")
def api_root():
    return {
        "title": "Multi-Source Cyclone Evolution & Impact Intelligence System API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_v1_endpoints": {
            "health": "/health",
            "auth": "/api/v1/auth",
            "storms": "/api/v1/storms",
            "observations": "/api/v1/observations",
            "evolution": "/api/v1/evolution",
            "prediction": "/api/v1/prediction",
            "gis": "/api/v1/gis",
            "scenario": "/api/v1/scenario",
            "models": "/api/v1/models",
            "system": "/api/v1/system"
        },
        "scientific_paradigm": "Observe -> Understand -> Predict -> Locate -> Simulate"
    }

# Mount frontend single page application
FRONTEND_DIR = BASE_DIR / "frontend" / "public"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
