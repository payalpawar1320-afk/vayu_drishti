import pytest
from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_live_cyclones_feed():
    res = client.get("/api/v1/storms/live")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    if len(data) > 0:
        first = data[0]
        assert "storm_id" in first
        assert "storm_name" in first
        assert first["storm_id"].startswith("LIVE_")
        assert first["peak_wind_kt"] > 0
        print(f"\n[TEST PASS] Live Cyclones Feed: Successfully loaded {len(data)} active storms, e.g. {first['storm_name']}")

def test_satellite_snapshot_metadata():
    res = client.get("/api/v1/observations/satellite/snapshot?date=2020-05-18&lat=16.5&lon=86.5&span_deg=8.0")
    assert res.status_code == 200
    data = res.json()
    assert "direct_snapshot_url" in data
    assert "tile_layer_url" in data
    assert "NASA" in data["source"]
    assert "MODIS_Terra_CorrectedReflectance_TrueColor" in data["direct_snapshot_url"]
    print(f"\n[TEST PASS] NASA GIBS Satellite Snapshot endpoint verified: {data['direct_snapshot_url'][:75]}...")
