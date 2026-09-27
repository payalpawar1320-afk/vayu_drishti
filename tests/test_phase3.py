import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.providers.ibtracs_provider import IBTrACSProvider
from ml.preprocessing.alignment import SpatioTemporalAlignmentEngine
from ml.evolution.fingerprint_extractor import EvolutionFingerprintExtractor
from ml.track_prediction.persistence_baseline import PersistenceTrackBaseline
from ml.intensity.pressure_trend_baseline import PhysicalIntensityTrendBaseline
from ml.evaluation.metrics import compute_track_metrics, compute_classification_metrics

def test_spatio_temporal_alignment():
    provider = IBTrACSProvider()
    amphan = provider.get_storm_detail("AMPHAN")
    assert amphan is not None

    aligner = SpatioTemporalAlignmentEngine(tolerance_hours=3.0)
    # Test alignment with observation at 2020-05-18 12:00:00
    target_time = "2020-05-18T12:00:00Z"
    fused_obs = aligner.align_observation(
        storm_id=amphan.storm_id,
        storm_name=amphan.storm_name,
        observation_time_iso=target_time,
        track_points=amphan.track_points
    )
    
    assert fused_obs.storm_name == "AMPHAN"
    assert fused_obs.quality_flags.temporal_delta_seconds <= 10800, "Should match within 3h tolerance"
    assert fused_obs.quality_flags.data_complete is True
    assert fused_obs.center["lat"] > 0
    assert "hursat_b1" in fused_obs.satellite_channels
    print(f"\n[TEST PASS] Spatio-Temporal Alignment: Matched Amphan at {fused_obs.center} (Delta: {fused_obs.quality_flags.temporal_delta_seconds}s)")

def test_evolution_fingerprint_extraction():
    provider = IBTrACSProvider()
    amphan = provider.get_storm_detail("AMPHAN")
    # Take a 24h segment during Amphan's rapid intensification (May 17-18)
    sub_points = [p for p in amphan.track_points if "2020-05-17" in p.iso_time or "2020-05-18" in p.iso_time][:8]
    assert len(sub_points) >= 4

    extractor = EvolutionFingerprintExtractor()
    fingerprint = extractor.extract_fingerprint(amphan.storm_id, sub_points)
    
    ind = fingerprint.indicators
    assert 0.0 <= ind.symmetry_score <= 1.0
    assert 0.0 <= ind.cloud_organization_score <= 1.0
    assert ind.central_dense_overcast_temp_k < 235.0, "Intense cyclone CDO must be cold cloud tops (< 235K)"
    assert ind.motion_vector.speed_knots > 0.0
    assert 0.0 <= ind.motion_vector.heading_degrees <= 360.0
    assert fingerprint.derived_evolution_phase in [
        "RAPID_ORGANIZATION", "STEADY_INTENSIFICATION", "MATURE_STABLE", "WEAKENING", "REORGANIZING / TRANSITIONING"
    ]
    print(f"\n[TEST PASS] Evolution Fingerprint: Phase={fingerprint.derived_evolution_phase}, Symmetry={ind.symmetry_score}, CDO Temp={ind.central_dense_overcast_temp_k}K, Speed={ind.motion_vector.speed_knots}kt, Heading={ind.motion_vector.heading_degrees}°")

def test_track_persistence_baseline():
    provider = IBTrACSProvider()
    fani = provider.get_storm_detail("FANI")
    assert fani is not None

    baseline = PersistenceTrackBaseline()
    sub_points = fani.track_points[10:15]
    forecast = baseline.predict_track(sub_points, horizons_hours=[6, 12, 24, 48])
    
    assert len(forecast) == 4
    for pt in forecast:
        assert pt.uncertainty_radius_km >= 35.0
        assert pt.latitude > 0 and pt.longitude > 0
        assert pt.predicted_wind_speed_kt > 0
    print(f"\n[TEST PASS] Persistence Track Forecast: 6h={forecast[0].latitude}°N, {forecast[0].longitude}°E | 24h={forecast[2].latitude}°N, {forecast[2].longitude}°E (Uncertainty: {forecast[2].uncertainty_radius_km}km)")

def test_physical_intensity_baseline_and_explainability():
    provider = IBTrACSProvider()
    amphan = provider.get_storm_detail("AMPHAN")
    sub_points = amphan.track_points[5:10]

    baseline = PhysicalIntensityTrendBaseline()
    trend_info, explain_info = baseline.predict_intensity_trend(sub_points, sst_c=30.5, shear_kt=9.0)
    
    assert trend_info.trend_label in ["STRENGTHENING", "STABLE", "WEAKENING"]
    assert trend_info.trend_confidence > 0.5
    assert len(explain_info.key_drivers) >= 2, "Must provide meteorological explainability factors"
    print(f"\n[TEST PASS] Intensity Trend & Explainability: Trend={trend_info.trend_label} (Conf: {trend_info.trend_confidence})")
    print(f"Explainability drivers: {explain_info.key_drivers[:2]}")

def test_benchmark_metrics_validity():
    metrics_file = BASE_DIR / "data" / "processed" / "benchmark_results.json"
    assert metrics_file.exists(), "Benchmark results file must exist"
    
    with open(metrics_file, "r") as f:
        data = json.load(f)
    
    assert "aggregate_track_metrics" in data
    assert "6h" in data["aggregate_track_metrics"]
    assert "24h" in data["aggregate_track_metrics"]
    assert data["aggregate_track_metrics"]["6h"]["mae_km"] < data["aggregate_track_metrics"]["24h"]["mae_km"], \
        "Track error must naturally increase with forecast horizon"
    assert "intensity_trend_metrics" in data
    assert "confusion_matrix" in data["intensity_trend_metrics"]
    print(f"\n[TEST PASS] Benchmark Metrics: 6h MAE={data['aggregate_track_metrics']['6h']['mae_km']}km, 24h MAE={data['aggregate_track_metrics']['24h']['mae_km']}km, Samples={data['aggregate_track_metrics']['6h']['samples_count']}")

if __name__ == "__main__":
    test_spatio_temporal_alignment()
    test_evolution_fingerprint_extraction()
    test_track_persistence_baseline()
    test_physical_intensity_baseline_and_explainability()
    test_benchmark_metrics_validity()
    print("\nALL PHASE 3 ALIGNMENT, EVOLUTION & BASELINE TESTS PASSED SUCCESSFULLY!")
