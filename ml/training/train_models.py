import sys
import json
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor

from backend.app.providers.ibtracs_provider import IBTrACSProvider
from ml.preprocessing.storm_splits import generate_storm_splits, SPLITS_FILE
from ml.preprocessing.sequence_builder import CycloneSequenceBuilder
from ml.evaluation.metrics import compute_track_metrics, compute_classification_metrics

MODELS_DIR = BASE_DIR / "models" / "trained"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
CHECKPOINT_JOBLIB = MODELS_DIR / "cyclone_temporal_nn.joblib"
CHECKPOINT_TORCH = MODELS_DIR / "cyclone_track_net.pt"

# Try loading torch
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import TensorDataset, DataLoader
    from ml.track_prediction.lstm_track_model import CycloneTemporalTrackNet
    TORCH_AVAILABLE = True
except Exception as e:
    TORCH_AVAILABLE = False
    print(f"[Notice] PyTorch unavailable ({e}); utilizing Scikit-Learn Deep MLP Multi-Horizon Engine.")

def prepare_split_dataset(provider: IBTrACSProvider, builder: CycloneSequenceBuilder, storms_list: list):
    X_all, Y_tr_all, Y_st_all = [], [], []
    for s_info in storms_list:
        detail = provider.get_storm_detail(s_info["storm_name"])
        if detail and len(detail.track_points) >= 12:
            x, y_tr, y_st = builder.extract_sequences_from_storm(detail.track_points)
            if len(x) > 0:
                X_all.append(x)
                Y_tr_all.append(y_tr)
                Y_st_all.append(y_st)

    if X_all:
        X = np.vstack(X_all)
        Y_tr = np.vstack(Y_tr_all)
        Y_st = np.concatenate(Y_st_all)
        return X, Y_tr, Y_st
    return np.empty((0, 5, 11)), np.empty((0, 8)), np.empty((0,))

def train():
    print("=" * 60)
    print("CYCLONE AI: MACHINE LEARNING MODEL TRAINING PIPELINE")
    print("=" * 60)

    # 1. Load or generate non-overlapping storm splits (Section 41)
    if not SPLITS_FILE.exists():
        splits = generate_storm_splits()
    else:
        with open(SPLITS_FILE, "r", encoding="utf-8") as f:
            splits = json.load(f)

    provider = IBTrACSProvider()
    builder = CycloneSequenceBuilder()

    print("\n[Data Preparation] Extracting multi-channel sequence tensors across splits...")
    X_train, Y_tr_train, Y_st_train = prepare_split_dataset(provider, builder, splits["train_storms"])
    X_val, Y_tr_val, Y_st_val = prepare_split_dataset(provider, builder, splits["val_storms"])
    X_test, Y_tr_test, Y_st_test = prepare_split_dataset(provider, builder, splits["test_storms"])

    print(f"  Train: {len(X_train)} sequences across {splits['train_count']} storms")
    print(f"  Val:   {len(X_val)} sequences across {splits['val_count']} storms")
    print(f"  Test:  {len(X_test)} sequences across {splits['test_count']} unseen storms ({[s['storm_name'] for s in splits['test_storms']]})")

    # Flatten (N, 5, 11) -> (N, 55) for MLP / sequence network input
    N_tr = len(X_train)
    X_train_flat = X_train.reshape(N_tr, -1)
    X_val_flat = X_val.reshape(len(X_val), -1)
    X_test_flat = X_test.reshape(len(X_test), -1)

    print("\n[Model Training] Fitting Deep Multi-Horizon Sequence Neural Network...")
    # Multi-Horizon Deep MLP: 55 inputs -> 128 -> 64 -> 32 -> 8 outputs
    mlp = MLPRegressor(
        hidden_layer_sizes=(128, 64, 32),
        activation="relu",
        solver="adam",
        alpha=0.001,
        learning_rate_init=0.003,
        max_iter=100,
        random_state=42,
        early_stopping=True,
        validation_fraction=0.15
    )
    regressor = MultiOutputRegressor(mlp)
    regressor.fit(X_train_flat, Y_tr_train)

    # Save trained checkpoint
    joblib.dump(regressor, CHECKPOINT_JOBLIB)
    print(f"  Trained model checkpoint successfully saved to: {CHECKPOINT_JOBLIB}")

    # 2. Evaluation on Held-Out Unseen Test Storms (Amphan, Fani, Tauktae)
    print("\n" + "=" * 60)
    print("EVALUATING TRAINED MODEL ON UNSEEN TEST STORMS (Amphan, Fani, Tauktae)")
    print("=" * 60)

    pred_deltas_test = regressor.predict(X_test_flat)

    test_eval_metrics = {}
    horizons = [6, 12, 24, 48]
    step_indices = [(0, 1), (2, 3), (4, 5), (6, 7)]

    for h, (lat_idx, lon_idx) in zip(horizons, step_indices):
        y_true_coords = []
        y_pred_coords = []

        for i in range(len(X_test)):
            t0_lat = X_test[i, -1, 0] * 35.0
            t0_lon = X_test[i, -1, 1] * 100.0

            true_lat = t0_lat + Y_tr_test[i, lat_idx]
            true_lon = t0_lon + Y_tr_test[i, lon_idx]

            pred_lat = t0_lat + pred_deltas_test[i, lat_idx]
            pred_lon = t0_lon + pred_deltas_test[i, lon_idx]

            y_true_coords.append((true_lat, true_lon))
            y_pred_coords.append((pred_lat, pred_lon))

        m = compute_track_metrics(y_true_coords, y_pred_coords)
        test_eval_metrics[f"{h}h"] = m
        print(f"  Horizon +{h:02d}h: Trained Model MAE = {m['mae_km']} km | RMSE = {m['rmse_km']} km (evaluated on {m['samples_count']} test samples)")

    benchmark_report_path = BASE_DIR / "data" / "processed" / "dl_benchmark_results.json"
    report = {
        "model_architecture": "Deep Multi-Horizon Sequence Neural Network (MLP 128-64-32)",
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "test_storms": [s["storm_name"] for s in splits["test_storms"]],
        "test_track_metrics": test_eval_metrics,
        "scientific_status": "EVALUATED_AGAINST_GROUND_TRUTH"
    }
    with open(benchmark_report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nComparative evaluation report saved to {benchmark_report_path}")
    return report

if __name__ == "__main__":
    train()
