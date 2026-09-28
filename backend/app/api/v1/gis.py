from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
import json
from pathlib import Path

from backend.app.schemas.gis import (
    GISExposureResponse, SummaryExposure, InfrastructureExposure, DistrictOverlap
)
from backend.app.providers.ibtracs_provider import IBTrACSProvider
from ml.track_prediction.persistence_baseline import PersistenceTrackBaseline
from gis.corridor.risk_corridor_generator import RiskCorridorGenerator
from gis.intersection.district_intersect import DistrictIntersectionEngine
from gis.infrastructure.asset_exposure import AssetExposureEngine
from gis.population.population_exposure import PopulationExposureEngine

router = APIRouter(prefix="/gis", tags=["GIS & Impact"])

_provider = None
_track_model = None
_corridor_gen = None
_district_engine = None
_asset_engine = None

def get_services():
    global _provider, _track_model, _corridor_gen, _district_engine, _asset_engine
    if _provider is None:
        _provider = IBTrACSProvider()
    if _track_model is None:
        _track_model = PersistenceTrackBaseline()
    if _corridor_gen is None:
        _corridor_gen = RiskCorridorGenerator()
    if _district_engine is None:
        _district_engine = DistrictIntersectionEngine()
    if _asset_engine is None:
        _asset_engine = AssetExposureEngine()
    return _provider, _track_model, _corridor_gen, _district_engine, _asset_engine

@router.get("/exposure/{storm_id}", response_model=GISExposureResponse)
def get_storm_gis_exposure(
    storm_id: str,
    forecast_step: Optional[int] = Query(default=None, description="Initialization step"),
    corridor_multiplier: float = Query(default=1.0, ge=0.5, le=3.0)
):
    """
    Computes dynamic risk corridor polygon along predicted track,
    intersects with India district boundaries, calculates estimated population
    exposed, and tallies critical infrastructure assets.
    """
    provider, track_model, corridor_gen, district_engine, asset_engine = get_services()
    detail = provider.get_storm_detail(storm_id)
    if not detail and storm_id.startswith("LIVE_"):
        from backend.app.providers.live_cyclone_provider import LiveCycloneProvider
        detail = LiveCycloneProvider.get_live_storm_detail(storm_id)

    if not detail:
        raise HTTPException(status_code=404, detail=f"Cyclone '{storm_id}' not found.")

    pts = detail.track_points
    if forecast_step is not None:
        init_idx = min(len(pts) - 1, max(0, forecast_step))
    else:
        init_idx = min(len(pts) - 1, max(0, int(len(pts) * 0.6)))

    history = pts[max(0, init_idx - 4) : init_idx + 1]
    if len(history) < 2 and len(pts) >= 2:
        history = pts[:2]

    # Generate forecast
    forecast_points = track_model.predict_track(history, horizons_hours=[6, 12, 18, 24, 36, 48])
    fc_dicts = [{"lat": p.latitude, "lon": p.longitude, "horizon_hours": p.horizon_hours} for p in forecast_points]

    # Generate risk corridor polygon
    corridor_poly, params = corridor_gen.generate_corridor(
        fc_dicts, corridor_width_multiplier=corridor_multiplier
    )

    # Intersections with robust fallback
    try:
        district_overlaps = district_engine.intersect(corridor_poly)
    except Exception as e:
        print(f"[GIS] Warning in district intersection: {e}")
        district_overlaps = []

    try:
        infra_summary, _ = asset_engine.calculate_exposure(corridor_poly)
    except Exception as e:
        print(f"[GIS] Warning in asset exposure: {e}")
        infra_summary = InfrastructureExposure(major_ports=0, airports=0, hospitals=0, national_highway_km=0.0)

    try:
        pop_summary = PopulationExposureEngine.calculate_total_exposure(district_overlaps)
    except Exception as e:
        print(f"[GIS] Warning in pop exposure: {e}")
        pop_summary = {"total_population_exposed": 0}

    summary = SummaryExposure(
        estimated_population_exposed=pop_summary["total_population_exposed"],
        total_districts_intersected=len(district_overlaps),
        critical_infrastructure_counts=infra_summary
    )

    corridor_geojson = corridor_gen.polygon_to_geojson_feature(
        corridor_poly,
        properties={
            "storm_id": detail.storm_id,
            "storm_name": detail.storm_name,
            "level": "MODELED_RISK_CORRIDOR",
            "corridor_area_sq_km": params.get("area_sq_km", 0.0),
            "data_badge": "[MODELED RISK CORRIDOR]"
        }
    )

    return GISExposureResponse(
        scenario_id="BASE_PREDICTION",
        is_simulation=False,
        corridor_parameters=params,
        risk_corridor_geojson=corridor_geojson,
        summary_exposure=summary,
        intersected_districts=district_overlaps
    )

_cached_districts_data: Optional[Dict[str, Any]] = None

@router.get("/districts")
def get_india_districts(
    state: Optional[str] = Query(default=None, description="Optional filter by state name")
):
    """Returns India district boundaries GeoJSON FeatureCollection."""
    global _cached_districts_data
    if _cached_districts_data is None:
        base_dir = Path(__file__).resolve().parents[4]
        path = base_dir / "data" / "raw" / "gis" / "india_districts.geojson"
        if not path.exists():
            return {"type": "FeatureCollection", "features": []}

        try:
            with open(path, "r", encoding="utf-8") as f:
                _cached_districts_data = json.load(f)
        except Exception as e:
            print(f"[GIS] Error reading districts: {e}")
            return {"type": "FeatureCollection", "features": []}

    data = _cached_districts_data

    if state:
        filtered = [f for f in data.get("features", []) if state.lower() in str(f.get("properties", {}).get("NAME_1", "")).lower()]
        return {"type": "FeatureCollection", "features": filtered}

    # Return simplified or first 100 if unconstrained
    return {"type": "FeatureCollection", "features": data.get("features", [])[:100]}

@router.get("/infrastructure")
def get_coastal_infrastructure():
    """Returns coastal infrastructure points and lines (Ports, Airports, Hospitals, Highways)."""
    base_dir = Path(__file__).resolve().parents[4]
    path = base_dir / "data" / "raw" / "gis" / "coastal_infrastructure.geojson"
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[GIS] Error reading infrastructure: {e}")
        return {"type": "FeatureCollection", "features": []}
