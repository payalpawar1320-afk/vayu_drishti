import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_api_root():
    res = client.get("/api")
    assert res.status_code == 200
    data = res.json()
    assert "api_v1_endpoints" in data
    print("\n[TEST PASS] API Root accessible at /api.")

def test_frontend_dashboard_html():
    res = client.get("/")
    assert res.status_code == 200
    assert "Cyclone Evolution & Impact Intelligence" in res.text
    print("\n[TEST PASS] Frontend HTML Dashboard accessible at /.")

def test_list_storms():
    res = client.get("/api/v1/storms?year=2020")
    assert res.status_code == 200
    storms = res.json()
    assert len(storms) > 0
    names = [s["storm_name"] for s in storms]
    assert "AMPHAN" in names
    print(f"\n[TEST PASS] Storms Endpoint: Listed {len(storms)} storms from 2020: {names[:4]}")

def test_storm_detail_and_timeline():
    res = client.get("/api/v1/storms/AMPHAN")
    assert res.status_code == 200
    detail = res.json()
    assert detail["storm_name"] == "AMPHAN"
    assert len(detail["track_points"]) >= 30
    assert detail["peak_wind_kt"] >= 100.0

    res_tl = client.get("/api/v1/storms/AMPHAN/timeline")
    assert res_tl.status_code == 200
    tl = res_tl.json()
    assert tl["total_steps"] == len(detail["track_points"])
    print(f"\n[TEST PASS] Storm Detail & Timeline: Cyclone Amphan with {tl['total_steps']} steps, Peak Wind {detail['peak_wind_kt']} kt.")

def test_fused_observation():
    res = client.get("/api/v1/observations/AMPHAN")
    assert res.status_code == 200
    obs = res.json()
    assert obs["storm_name"] == "AMPHAN"
    assert "hursat_b1" in obs["satellite_channels"]
    assert "environmental_features" in obs
    assert obs["center"]["lat"] > 0
    print(f"\n[TEST PASS] Fused Observation: Matched center {obs['center']} with satellite channels {list(obs['satellite_channels'].keys())}")

def test_evolution_endpoints():
    res = client.get("/api/v1/evolution/AMPHAN")
    assert res.status_code == 200
    fp = res.json()
    assert "indicators" in fp
    assert fp["indicators"]["symmetry_score"] > 0
    assert fp["indicators"]["motion_vector"]["speed_knots"] > 0
    assert "derived_evolution_phase" in fp

    res_prog = client.get("/api/v1/evolution/AMPHAN/progression")
    assert res_prog.status_code == 200
    prog = res_prog.json()
    assert prog["total_progression_steps"] > 5
    print(f"\n[TEST PASS] Evolution Endpoints: Phase={fp['derived_evolution_phase']}, Progression steps={prog['total_progression_steps']}")

def test_prediction_endpoint():
    res = client.get("/api/v1/prediction/AMPHAN")
    assert res.status_code == 200
    pred = res.json()
    assert len(pred["forecast_points"]) == 6
    assert pred["intensity_trend"]["trend_label"] in ["STRENGTHENING", "STABLE", "WEAKENING"]
    assert len(pred["explainability"]["key_drivers"]) >= 2
    print(f"\n[TEST PASS] Prediction Endpoint: 6h={pred['forecast_points'][0]['latitude']}N, 48h={pred['forecast_points'][-1]['latitude']}N | Trend={pred['intensity_trend']['trend_label']}")

def test_gis_exposure_endpoint():
    res = client.get("/api/v1/gis/exposure/AMPHAN")
    assert res.status_code == 200
    gis = res.json()
    assert gis["risk_corridor_geojson"]["type"] == "Feature"
    assert gis["summary_exposure"]["estimated_population_exposed"] > 0
    assert len(gis["intersected_districts"]) > 0
    top = gis["intersected_districts"][0]
    print(f"\n[TEST PASS] GIS Exposure: Total Pop Exposed={gis['summary_exposure']['estimated_population_exposed']:,}, Intersected Districts={len(gis['intersected_districts'])}, Top={top['district_name']} ({top['area_overlap_pct']}%)")

def test_scenario_simulation_endpoint():
    payload = {
        "storm_id": "AMPHAN",
        "track_shift_direction": "WEST",
        "track_shift_km": 50.0,
        "intensity_modifier": "HIGHER",
        "corridor_width_multiplier": 1.2
    }
    res = client.post("/api/v1/scenario/simulate", json=payload)
    assert res.status_code == 200
    sim = res.json()
    assert sim["simulation_flag"].startswith("SIMULATED_SCENARIO")
    assert "population_delta" in sim["exposure_delta"]
    assert len(sim["districts_added"]) > 0
    print(f"\n[TEST PASS] Scenario Simulation: Base Pop={sim['base_exposure']['estimated_population_exposed']:,} -> Sim Pop={sim['simulated_exposure']['estimated_population_exposed']:,} (Delta: {sim['exposure_delta']['population_delta']:,})")

def test_model_benchmarks_and_system_status():
    res_b = client.get("/api/v1/models/benchmarks")
    assert res_b.status_code == 200
    b = res_b.json()
    assert "aggregate_track_metrics" in b

    res_s = client.get("/api/v1/system/status")
    assert res_s.status_code == 200
    s = res_s.json()
    assert s["system_status"] == "ONLINE"
    assert len(s["active_data_sources"]) >= 4
    print(f"\n[TEST PASS] Models & System Status: System Status={s['system_status']}, Active Sources={len(s['active_data_sources'])}, 6h MAE={b['aggregate_track_metrics']['6h']['mae_km']}km")

def test_eye_structure_endpoint():
    res = client.get("/api/v1/evolution/AMPHAN/eye_structure")
    assert res.status_code == 200
    eye = res.json()
    assert "eye_detected" in eye
    assert eye["eye_detected"] is True
    assert eye["eye_radius_km"] > 0
    assert eye["eyewall_radius_km"] > eye["eye_radius_km"]
    assert eye["cdo_radius_km"] > eye["eyewall_radius_km"]
    assert "classification" in eye
    print(f"\n[TEST PASS] Eye Structure: Detected={eye['eye_detected']}, Class={eye['classification']}, Eye R={eye['eye_radius_km']}km, Eyewall RMW={eye['eyewall_radius_km']}km, CDO R={eye['cdo_radius_km']}km")

if __name__ == "__main__":
    test_api_root()
    test_list_storms()
    test_storm_detail_and_timeline()
    test_fused_observation()
    test_evolution_endpoints()
    test_eye_structure_endpoint()
    test_prediction_endpoint()
    test_gis_exposure_endpoint()
    test_scenario_simulation_endpoint()
    test_model_benchmarks_and_system_status()
    print("\nALL PHASE 4 FASTAPI BACKEND INTEGRATION TESTS PASSED SUCCESSFULLY!")

