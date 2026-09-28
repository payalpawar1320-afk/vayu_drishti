"""
Test suite for VAYU-DRISHTI Authority Authentication, Role-Based Access Control,
and Public Citizen View availability.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from starlette.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_authorities_catalog():
    """Ensure catalog lists official authority designations without passwords."""
    res = client.get("/api/v1/auth/authorities-catalog")
    assert res.status_code == 200
    catalog = res.json()
    assert len(catalog) >= 4
    emails = [c["official_email"] for c in catalog]
    assert "director.ndma@gov.in" in emails
    assert "control.odisha@sdma.gov.in" in emails
    # Ensure no secrets leaked
    for item in catalog:
        assert "password" not in item
        assert "hash" not in item
    print("\n[TEST PASS] Authorities Catalog: 4 official authority departments listed securely.")

def test_invalid_credentials_rejected():
    """Ensure invalid credentials are mathematically rejected."""
    res = client.post("/api/v1/auth/login", json={
        "email": "director.ndma@gov.in",
        "password": "WrongPassword_2026!"
    })
    assert res.status_code == 401
    print("\n[TEST PASS] Invalid authority credentials rejected with HTTP 401.")

def test_authority_login_success():
    """Ensure official authority account authenticates and receives verified role."""
    res = client.post("/api/v1/auth/login", json={
        "email": "director.ndma@gov.in",
        "password": "NDMA_National_2026!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["role"] in ["AUTHORITY_NDMA", "AUTHORITY"]
    assert data["user"]["is_authority"] is True
    print(f"\n[TEST PASS] Authority Login: Authenticated '{data['user']['full_name']}' as {data['user']['role']}.")

    # Test /auth/me with Bearer token
    token = data["access_token"]
    res_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    user_me = res_me.json()
    assert user_me["email"] == "director.ndma@gov.in"
    assert user_me["is_authority"] is True
    print("\n[TEST PASS] Authority Session Verification (/auth/me) passed.")

def test_citizen_rejected_from_authority_login():
    """Ensure citizen account cannot authenticate into the restricted Authority portal."""
    res = client.post("/api/v1/auth/login", json={
        "email": "citizen.priya.pur@gmail.com",
        "password": "CitizenPassword_2026!"
    })
    assert res.status_code in [401, 403]
    print("\n[TEST PASS] Citizen account strictly prohibited from Authority Portal.")

def test_state_authority_sdma_login():
    """Test State Disaster Authority login (Odisha OSDMA)."""
    res = client.post("/api/v1/auth/login", json={
        "email": "control.odisha@sdma.gov.in",
        "password": "OSDMA_Odisha_2026!"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "SDMA" in data["user"]["role"]
    print(f"\n[TEST PASS] State Authority Login: {data['user']['full_name']} ({data['user']['role']}).")

def test_frontend_authority_and_citizen_pages():
    """Ensure HTML includes Citizen View, Authority Login, and Header controls."""
    res = client.get("/")
    assert res.status_code == 200
    html = res.text

    # Authority Login Page
    assert 'id="page-auth-login"' in html
    assert 'Authority Access Portal' in html
    assert 'id="form-authority-login"' in html
    assert 'id="auth-input-email"' in html
    assert 'id="auth-input-password"' in html

    # Citizen View Page
    assert 'id="page-citizen"' in html
    assert 'Citizen View' in html
    assert 'id="citizen-leaflet-map"' in html
    assert 'id="citizen-district-select"' in html
    assert 'id="citizen-storm-select"' in html
    assert '1078' in html # National helpline

    # Header and Hero Access Flow buttons
    assert 'id="btn-header-logout"' in html
    assert 'id="btn-home-citizen"' in html
    assert 'id="btn-home-authority"' in html
    print("\n[TEST PASS] Frontend includes Authority Login, Citizen View, and Access Flow controls.")

def test_dynamic_citizen_data_sources():
    """Verify backend endpoints feeding the dynamic Citizen View (storms & GIS exposure)."""
    # 1. Storm Detail for dynamic advisory
    res_storm = client.get("/api/v1/storms/AMPHAN")
    assert res_storm.status_code == 200
    st = res_storm.json()
    assert "storm_name" in st
    assert len(st["track_points"]) > 0

    # 2. GIS Exposure for dynamic risk corridor and intersected districts
    res_gis = client.get("/api/v1/gis/exposure/AMPHAN")
    assert res_gis.status_code == 200
    gis = res_gis.json()
    assert "risk_corridor_geojson" in gis
    assert len(gis["intersected_districts"]) > 0
    top_district = gis["intersected_districts"][0]
    assert "district_name" in top_district
    assert "area_overlap_pct" in top_district
    assert "estimated_population" in top_district
    assert "estimated_population_exposed" in gis["summary_exposure"]
    print(f"\n[TEST PASS] Dynamic Citizen Data: Verified real-time GIS exposure for {st['storm_name']} across {len(gis['intersected_districts'])} districts (Top: {top_district['district_name']} at {top_district['area_overlap_pct']}% overlap, Pop: {top_district['estimated_population']:,}).")

