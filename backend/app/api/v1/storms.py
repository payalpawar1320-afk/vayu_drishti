from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from backend.app.schemas.storm import StormSummary, StormDetail
from backend.app.providers.ibtracs_provider import IBTrACSProvider
from backend.app.providers.live_cyclone_provider import LiveCycloneProvider

router = APIRouter(prefix="/storms", tags=["Storms"])

# Singleton provider instance
_provider = None

def get_provider() -> IBTrACSProvider:
    global _provider
    if _provider is None:
        _provider = IBTrACSProvider()
    return _provider

@router.get("/live", response_model=List[StormSummary])
def list_live_storms():
    """
    Returns real-time active tropical cyclones from NOAA / JTWC live feed.
    """
    return LiveCycloneProvider.get_active_storms()

@router.get("/live/{storm_id}", response_model=StormDetail)
def get_live_storm_detail(storm_id: str):
    """
    Returns real-time best-track & forecast observations for an active cyclone.
    """
    detail = LiveCycloneProvider.get_live_storm_detail(storm_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Active cyclone '{storm_id}' not found in live feed.")
    return detail

@router.get("", response_model=List[StormSummary])
def list_storms(
    basin: Optional[str] = Query(default="NI", description="Ocean Basin (e.g. NI)"),
    year: Optional[int] = Query(default=None, description="Year filter (e.g. 2020)"),
    limit: int = Query(default=50, ge=1, le=200, description="Max storms to return")
):
    """Returns catalog of historical North Indian Ocean tropical cyclones from official NOAA IBTrACS."""
    provider = get_provider()
    storms = provider.get_storms(basin=basin, year=year)
    return storms[:limit]

@router.get("/{storm_id}", response_model=StormDetail)
def get_storm_detail(storm_id: str):
    """Returns complete lifecycle and best-track observations for a specific cyclone (historical or live)."""
    if storm_id.startswith("LIVE_"):
        detail = LiveCycloneProvider.get_live_storm_detail(storm_id)
        if detail:
            return detail

    provider = get_provider()
    detail = provider.get_storm_detail(storm_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Cyclone '{storm_id}' not found in official catalog.")
    return detail

@router.get("/{storm_id}/timeline")
def get_storm_timeline(storm_id: str):
    """Returns sequential time steps with coordinates, wind, pressure, and stage classification."""
    if storm_id.startswith("LIVE_"):
        detail = LiveCycloneProvider.get_live_storm_detail(storm_id)
        if not detail:
            raise HTTPException(status_code=404, detail=f"Live cyclone '{storm_id}' not found.")
        timeline = [
            {
                "step_index": idx,
                "iso_time": pt.iso_time,
                "latitude": pt.latitude,
                "longitude": pt.longitude,
                "wind_speed_kt": pt.max_sustained_wind_kt,
                "pressure_mb": pt.min_central_pressure_mb,
                "imd_category": pt.nature or "Active Storm"
            }
            for idx, pt in enumerate(detail.track_points)
        ]
        return {
            "storm_id": storm_id,
            "total_steps": len(timeline),
            "steps": timeline
        }

    provider = get_provider()
    timeline = provider.get_timeline(storm_id)
    if not timeline:
        raise HTTPException(status_code=404, detail=f"Timeline for storm '{storm_id}' not found.")
    return {
        "storm_id": storm_id,
        "total_steps": len(timeline),
        "steps": timeline
    }
