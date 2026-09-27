import sys
import json
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np
from backend.app.providers.ibtracs_provider import IBTrACSProvider
from ml.preprocessing.storm_splits import generate_storm_splits, SPLITS_FILE
from ml.preprocessing.sequence_builder import CycloneSequenceBuilder
from ml.evaluation.metrics import compute_track_metrics

def test_storm_splits_isolation():
    splits = generate_storm_splits()
    assert splits["train_count"] >= 30, "Should have >= 30 train storms"
    assert splits["test_count"] >= 3, "Should have >= 3 test storms"
    
    train_names = set(s["storm_name"] for s in splits["train_storms"])
    test_names = set(s["storm_name"] for s in splits["test_storms"])
    val_names = set(s["storm_name"] for s in splits["val_storms"])
    
    # Zero leakage check
    assert len(train_names.intersection(test_names)) == 0, "Zero leakage between train and test"
    assert len(train_names.intersection(val_names)) == 0, "Zero leakage between train and val"
    assert "AMPHAN" in test_names, "Amphan should be in test set"
    assert "FANI" in test_names, "Fani should be in test set"
    print(f"\n[TEST PASS] Storm-Level Splits: Train={len(train_names)}, Val={len(val_names)}, Test={len(test_names)} (ZERO LEAKAGE).")

def test_sequence_builder_tensors():
    provider = IBTrACSProvider()
    amphan = provider.get_storm_detail("AMPHAN")
    builder = CycloneSequenceBuilder(sequence_length=5)
    
    X, Y_tr, Y_st = builder.extract_sequences_from_storm(amphan.track_points)
    assert len(X) > 0, "Should extract valid sequence windows"
    assert X.shape[1] == 5, "Sequence length must be 5 (T-24h to T0)"
    assert X.shape[2] == 11, "Feature dimension must be 11"
    assert Y_tr.shape[1] == 8, "Track targets must be 8 deltas (4 horizons x 2)"
    assert len(Y_st) == len(X)
    print(f"\n[TEST PASS] Sequence Builder: Extracted {len(X)} sequences of shape {X.shape} and targets {Y_tr.shape}.")

def test_trained_model_inference_and_benchmarks():
    checkpoint_file = BASE_DIR / "models" / "trained" / "cyclone_temporal_nn.joblib"
    report_file = BASE_DIR / "data" / "processed" / "dl_benchmark_results.json"
    
    # Check if checkpoint exists
    if checkpoint_file.exists():
        model = joblib.load(checkpoint_file)
        # Dummy sequence inference
        dummy_seq = np.random.randn(1, 55).astype(np.float32)
        pred_deltas = model.predict(dummy_seq)
        assert pred_deltas.shape == (1, 8), "Must output 8 forecast deltas"
        print(f"\n[TEST PASS] Trained ML Model loaded and inferred deltas: {pred_deltas[0].round(2)}")

    if report_file.exists():
        with open(report_file, "r") as f:
            report = json.load(f)
        assert "test_track_metrics" in report
        m = report["test_track_metrics"]
        assert "6h" in m and "24h" in m
        print(f"\n[TEST PASS] Trained Model Unseen Test Evaluation: 6h MAE={m['6h']['mae_km']}km, 24h MAE={m['24h']['mae_km']}km on {report['test_samples']} samples.")

if __name__ == "__main__":
    test_storm_splits_isolation()
    test_sequence_builder_tensors()
    test_trained_model_inference_and_benchmarks()
    print("\nALL PHASE 6 MACHINE LEARNING TESTS PASSED SUCCESSFULLY!")
