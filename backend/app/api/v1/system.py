from fastapi import APIRouter
import yaml
from pathlib import Path
from datetime import datetime, timezone

router = APIRouter(prefix="/system", tags=["System & Sources"])

@router.get("/status")
def get_system_status():
    """
    Returns system status, active data sources, mode (HISTORICAL DEMO vs LIVE),
    and operational data freshness timestamps per Sections 47, 48, 66 of SPEC.md.
    """
    now_utc = datetime.now(timezone.utc).isoformat()
    from backend.app.providers.mosdac_provider import MOSDACProvider
    mosdac_info = MOSDACProvider().get_connection_status()

    return {
        "system_title": "Multi-Source Cyclone Evolution & Impact Intelligence System",
        "system_status": "ONLINE",
        "operational_mode": "HISTORICAL_DEMO_MODE",
        "active_data_sources": [
            {"name": "NOAA IBTrACS", "version": "v04r01", "status": "CONNECTED", "badge": "[NOAA IBTrACS]"},
            {"name": "NOAA HURSAT-B1", "version": "v06", "status": "CALIBRATED_ONLINE", "badge": "[NOAA HURSAT-B1]"},
            {"name": "Copernicus ERA5", "version": "Hourly Single Levels", "status": "ENVIRONMENTAL_ACTIVE", "badge": "[ERA5]"},
            {"name": "NWIC / GSI Districts", "version": "Census 2011 Administrative", "status": "GIS_ACTIVE", "badge": "[OFFICIAL DISTRICTS]"},
            {"name": "WorldPop / Census India", "version": "2011/2020", "status": "EXPOSURE_ONLINE", "badge": "[WORLDPOP]"},
            {"name": "OpenStreetMap", "version": "Geofabrik India", "status": "INFRASTRUCTURE_ACTIVE", "badge": "[OSM]"},
            {"name": "ISRO MOSDAC (INSAT)", "version": "INSAT-3D/3DR/3DS", "status": mosdac_info["status"], "badge": "[MOSDAC/ISRO]"}
        ],
        "server_timestamp_utc": now_utc,
        "disclaimer_badge": "DISASTER DECISION-SUPPORT PROTOTYPE (NOT AN OFFICIAL METEOROLOGICAL WARNING)"
    }

@router.get("/sources")
def get_data_sources_registry():
    """Returns official dataset sources, official links, citations, and licenses per Sections 65, 85."""
    base_dir = Path(__file__).resolve().parents[4]
    path = base_dir / "configs" / "dataset_sources.yaml"
    if not path.exists():
        return {"error": "dataset_sources.yaml not found"}

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
