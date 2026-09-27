import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import geopandas as gpd

from backend.app.schemas import (
    StormSummary, StormDetail, BestTrackPoint,
    FusedObservation, EvolutionFingerprint,
    TrackIntensityPrediction, GISExposureResponse
)
from backend.app.providers.ibtracs_provider import IBTrACSProvider
from ml.preprocessing.netcdf_parser import HursatNetCDFParser

BASE_DIR = Path(__file__).resolve().parent.parent

def test_ibtracs_dataset_exists_and_loads():
    csv_file = BASE_DIR / "data" / "raw" / "ibtracs" / "ibtracs_NI_latest.csv"
    assert csv_file.exists(), "IBTrACS raw file should exist"
    assert csv_file.stat().st_size > 1000000, "IBTrACS raw file should be > 1MB"
    
    provider = IBTrACSProvider(csv_file)
    storms_2020 = provider.get_storms(year=2020)
    assert len(storms_2020) > 0, "Should have storms in 2020"
    
    # Check Cyclone Amphan
    amphan = provider.get_storm_detail("AMPHAN")
    assert amphan is not None, "Cyclone Amphan must be found"
    assert amphan.storm_name == "AMPHAN"
    assert amphan.year == 2020
    assert len(amphan.track_points) >= 30, "Amphan should have at least 30 best track points"
    assert amphan.peak_wind_kt >= 90.0, "Amphan peak wind should be high"
    print(f"\n[TEST PASS] Ingested Cyclone Amphan: {len(amphan.track_points)} track points, Peak Wind: {amphan.peak_wind_kt} kt")

def test_india_districts_geojson():
    geojson_file = BASE_DIR / "data" / "raw" / "gis" / "india_districts.geojson"
    assert geojson_file.exists(), "Districts GeoJSON should exist"
    gdf = gpd.read_file(geojson_file)
    assert len(gdf) >= 500, f"Should have >= 500 districts, found {len(gdf)}"
    
    # Check presence of key coastal states
    states = gdf['NAME_1'].dropna().unique().tolist()
    assert "West Bengal" in states, "West Bengal should be present"
    assert any("Orissa" in s or "Odisha" in s for s in states), "Odisha should be present"
    assert "Andhra Pradesh" in states, "Andhra Pradesh should be present"
    assert "Tamil Nadu" in states, "Tamil Nadu should be present"
    assert "Gujarat" in states, "Gujarat should be present"
    print(f"\n[TEST PASS] Ingested India Districts GeoJSON: {len(gdf)} districts across all coastal states.")

def test_population_and_infrastructure_data():
    pop_file = BASE_DIR / "data" / "raw" / "gis" / "district_population_reference.json"
    infra_file = BASE_DIR / "data" / "raw" / "gis" / "coastal_infrastructure.geojson"
    
    assert pop_file.exists(), "Population reference file should exist"
    assert infra_file.exists(), "Infrastructure GeoJSON should exist"
    
    with open(pop_file, "r") as f:
        pop_data = json.load(f)
    assert "South 24 Parganas" in pop_data
    assert "Baleshwar" in pop_data
    assert pop_data["South 24 Parganas"] > 5000000
    
    infra_gdf = gpd.read_file(infra_file)
    assert len(infra_gdf) >= 15, f"Should have >= 15 infrastructure assets, found {len(infra_gdf)}"
    categories = infra_gdf['category'].unique().tolist()
    assert "PORT" in categories
    assert "AIRPORT" in categories
    assert "HOSPITAL" in categories
    print(f"\n[TEST PASS] Ingested {len(pop_data)} district populations and {len(infra_gdf)} critical infrastructure assets.")

def test_pydantic_data_contracts():
    obs = FusedObservation(
        storm_id="2020136N10088",
        storm_name="AMPHAN",
        target_timestamp="2020-05-18T12:00:00Z",
        center={"lat": 15.2, "lon": 86.5, "source": "IBTrACS"},
        data_source_badge="NOAA IBTrACS + NOAA HURSAT-B1"
    )
    assert obs.storm_name == "AMPHAN"
    assert obs.center["lat"] == 15.2
    
    # Serialization check
    json_str = obs.model_dump_json()
    assert "2020136N10088" in json_str
    print("\n[TEST PASS] Pydantic data contract validated and serialized.")

def test_hursat_radiance_calibration():
    grid, ind = HursatNetCDFParser.generate_calibrated_ir_matrix(15.2, 86.5, 120.0, 930.0)
    assert grid.shape == (151, 151)
    assert 185.0 <= ind["cdo_min_temp_k"] <= 215.0, "CDO minimum temp should reflect intense cyclone"
    assert ind["symmetry_score"] > 0.5
    print(f"\n[TEST PASS] HURSAT IR matrix calibrated: CDO Min Temp = {ind['cdo_min_temp_k']} K, Symmetry = {ind['symmetry_score']}")

if __name__ == "__main__":
    test_ibtracs_dataset_exists_and_loads()
    test_india_districts_geojson()
    test_population_and_infrastructure_data()
    test_pydantic_data_contracts()
    test_hursat_radiance_calibration()
    print("\nALL PHASE 1 TESTS PASSED SUCCESSFULLY!")
