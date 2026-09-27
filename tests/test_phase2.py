import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from shapely.geometry import Polygon
from gis.corridor.risk_corridor_generator import RiskCorridorGenerator
from gis.intersection.district_intersect import DistrictIntersectionEngine
from gis.infrastructure.asset_exposure import AssetExposureEngine
from gis.population.population_exposure import PopulationExposureEngine
from gis.scenario.impact_shift_engine import ImpactShiftSimulator
from backend.app.schemas.gis import ScenarioShiftRequest

def test_corridor_generator_geometry():
    gen = RiskCorridorGenerator(base_radius_km=40.0, hourly_expansion_km=2.5)
    pts = [
        {"lat": 14.0, "lon": 86.0, "horizon_hours": 0},
        {"lat": 18.0, "lon": 87.0, "horizon_hours": 24},
        {"lat": 22.0, "lon": 88.5, "horizon_hours": 48}
    ]
    poly, params = gen.generate_corridor(pts)
    assert isinstance(poly, Polygon), "Corridor must be a Polygon"
    assert poly.is_valid, "Corridor Polygon must be topologically valid"
    assert not poly.is_empty, "Corridor Polygon must not be empty"
    assert params["area_sq_km"] > 50000.0, "Cone of uncertainty area should expand realistically"
    
    geojson = gen.polygon_to_geojson_feature(poly)
    assert geojson["type"] == "Feature"
    assert geojson["geometry"]["type"] == "Polygon"
    print(f"\n[TEST PASS] Risk Corridor Generated: {params['area_sq_km']} sq km cone of uncertainty.")

def test_district_intersection_calculation():
    engine = DistrictIntersectionEngine()
    gen = RiskCorridorGenerator()
    # Track making landfall near West Bengal / Odisha border
    pts = [
        {"lat": 19.5, "lon": 87.2, "horizon_hours": 12},
        {"lat": 21.6, "lon": 88.3, "horizon_hours": 24}
    ]
    poly, _ = gen.generate_corridor(pts)
    overlaps = engine.intersect(poly)
    
    assert len(overlaps) > 0, "Should intersect at least one coastal district"
    dist_names = [d.district_name for d in overlaps]
    assert any("Midnapore" in d or "24 Parganas" in d or "Baleshwar" in d for d in dist_names), \
        "Expected landfall districts (Midnapore / 24 Parganas / Balasore) in corridor"
    
    # Check overlap calculation properties
    top_district = overlaps[0]
    assert 0.0 < top_district.area_overlap_pct <= 100.0
    assert top_district.risk_classification in ["CRITICAL_LANDFALL", "HIGH", "MODERATE", "LOW"]
    assert top_district.estimated_population > 0
    print(f"\n[TEST PASS] District Intersection: {len(overlaps)} districts intersected. Top: {top_district.district_name} ({top_district.area_overlap_pct}% overlap, {top_district.estimated_population:,} pop exposed)")

def test_infrastructure_exposure_tally():
    asset_engine = AssetExposureEngine()
    gen = RiskCorridorGenerator()
    pts = [
        {"lat": 19.5, "lon": 87.2, "horizon_hours": 12},
        {"lat": 21.6, "lon": 88.3, "horizon_hours": 24}
    ]
    poly, _ = gen.generate_corridor(pts)
    summary, assets = asset_engine.calculate_exposure(poly)
    
    assert summary.major_ports >= 1, "Expected at least 1 major port in the landfall region (Haldia/Dhamra)"
    assert summary.hospitals >= 1, "Expected hospitals in coastal zone"
    assert len(assets) > 0
    print(f"\n[TEST PASS] Infrastructure Exposure: {summary.major_ports} ports, {summary.airports} airports, {summary.hospitals} hospitals, {summary.national_highway_km} km highways.")

def test_impact_shift_simulator():
    simulator = ImpactShiftSimulator()
    pts = [
        {"lat": 18.0, "lon": 86.8, "horizon_hours": 0},
        {"lat": 20.0, "lon": 87.5, "horizon_hours": 12},
        {"lat": 22.0, "lon": 88.4, "horizon_hours": 24}
    ]
    req = ScenarioShiftRequest(
        storm_id="2020136N10088",
        track_shift_direction="WEST",
        track_shift_km=50.0,
        intensity_modifier="HIGHER",
        corridor_width_multiplier=1.2
    )
    res = simulator.simulate(pts, req)
    
    assert res.simulation_flag.startswith("SIMULATED_SCENARIO"), "Simulation flag must be prominent"
    assert res.base_exposure.estimated_population_exposed > 0
    assert res.simulated_exposure.estimated_population_exposed > 0
    assert "population_delta" in res.exposure_delta
    assert len(res.districts_added) > 0, "Westward shift should bring in additional Odisha districts"
    print(f"\n[TEST PASS] Impact Shift Simulator: Base={res.base_exposure.estimated_population_exposed:,} -> Sim={res.simulated_exposure.estimated_population_exposed:,} (Delta: {res.exposure_delta['population_delta']:,})")
    print(f"Districts Added: {res.districts_added[:4]}...")

if __name__ == "__main__":
    test_corridor_generator_geometry()
    test_district_intersection_calculation()
    test_infrastructure_exposure_tally()
    test_impact_shift_simulator()
    print("\nALL PHASE 2 GIS & SIMULATOR TESTS PASSED SUCCESSFULLY!")
