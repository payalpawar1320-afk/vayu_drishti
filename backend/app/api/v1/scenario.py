from fastapi import APIRouter, HTTPException, Body

from backend.app.schemas.gis import ScenarioShiftRequest, ScenarioShiftResponse
from backend.app.providers.ibtracs_provider import IBTrACSProvider
from ml.track_prediction.persistence_baseline import PersistenceTrackBaseline
from gis.scenario.impact_shift_engine import ImpactShiftSimulator

router = APIRouter(prefix="/scenario", tags=["Impact Shift Simulator"])

_provider = None
_track_model = None
_simulator = None

def get_services():
    global _provider, _track_model, _simulator
    if _provider is None:
        _provider = IBTrACSProvider()
    if _track_model is None:
        _track_model = PersistenceTrackBaseline()
    if _simulator is None:
        _simulator = ImpactShiftSimulator()
    return _provider, _track_model, _simulator

@router.post("/simulate", response_model=ScenarioShiftResponse)
def simulate_impact_shift(request: ScenarioShiftRequest = Body(...)):
    """
    Executes real-time scenario simulation for 'What changes if the cyclone path changes?'
    Computes comparative population deltas, newly added districts, dropped districts,
    and infrastructure changes under alternative parametric scenarios.
    Strictly marked as SIMULATED_SCENARIO (NOT AN OFFICIAL FORECAST).
    """
    provider, track_model, simulator = get_services()
    detail = provider.get_storm_detail(request.storm_id)
    if not detail and request.storm_id.startswith("LIVE_"):
        from backend.app.providers.live_cyclone_provider import LiveCycloneProvider
        detail = LiveCycloneProvider.get_live_storm_detail(request.storm_id)

    if not detail:
        raise HTTPException(status_code=404, detail=f"Cyclone '{request.storm_id}' not found.")

    pts = detail.track_points
    init_idx = max(4, int(len(pts) * 0.6))
    history = pts[max(0, init_idx - 4) : init_idx + 1]

    # Forecast points
    forecast_points = track_model.predict_track(history, horizons_hours=[6, 12, 18, 24, 36, 48])
    fc_dicts = [{"lat": p.latitude, "lon": p.longitude, "horizon_hours": p.horizon_hours} for p in forecast_points]

    response = simulator.simulate(fc_dicts, request)
    return response
