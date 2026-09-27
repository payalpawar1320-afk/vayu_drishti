import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def compute_track_metrics(y_true: List[Tuple[float, float]], y_pred: List[Tuple[float, float]]) -> Dict[str, float]:
    """
    Computes genuine Great-Circle Distance error (Haversine), MAE, and RMSE in km.
    y_true: list of (lat, lon) true coordinates
    y_pred: list of (lat, lon) predicted coordinates
    """
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        raise ValueError("y_true and y_pred must have matching non-zero lengths")

    haversine_errors = []
    lat_errors = []
    lon_errors = []

    for (lat_t, lon_t), (lat_p, lon_p) in zip(y_true, y_pred):
        # Haversine distance
        phi1 = np.radians(lat_t)
        phi2 = np.radians(lat_p)
        dphi = np.radians(lat_p - lat_t)
        dlam = np.radians(lon_p - lon_t)

        a = np.sin(dphi / 2)**2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlam / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        dist_km = 6371.0 * c

        haversine_errors.append(dist_km)
        lat_errors.append(abs(lat_p - lat_t))
        lon_errors.append(abs(lon_p - lon_t))

    errors_arr = np.array(haversine_errors)

    return {
        "mae_km": round(float(np.mean(errors_arr)), 2),
        "rmse_km": round(float(np.sqrt(np.mean(errors_arr**2))), 2),
        "min_error_km": round(float(np.min(errors_arr)), 2),
        "max_error_km": round(float(np.max(errors_arr)), 2),
        "lat_mae_deg": round(float(np.mean(lat_errors)), 3),
        "lon_mae_deg": round(float(np.mean(lon_errors)), 3),
        "samples_count": len(y_true)
    }

def compute_classification_metrics(y_true: List[str], y_pred: List[str], labels: List[str] = None) -> Dict[str, Any]:
    """
    Computes actual classification metrics: Accuracy, Precision, Recall, F1, and Confusion Matrix.
    """
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        raise ValueError("y_true and y_pred must have matching non-zero lengths")

    if labels is None:
        labels = sorted(list(set(y_true + y_pred)))

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    rec = recall_score(y_true, y_pred, average='weighted', zero_division=0)
    f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    return {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "labels": labels,
        "confusion_matrix": cm,
        "samples_count": len(y_true)
    }
