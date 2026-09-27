from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

router = APIRouter(prefix="/models", tags=["Model Performance & Registry"])

@router.get("/benchmarks")
def get_model_benchmarks():
    """
    Returns actual, un-fabricated model evaluation metrics calculated on
    unseen historical North Indian Ocean cyclones per Section 40 of SPEC.md.
    """
    base_dir = Path(__file__).resolve().parents[4]
    baseline_path = base_dir / "data" / "processed" / "benchmark_results.json"
    dl_path = base_dir / "data" / "processed" / "dl_benchmark_results.json"

    result = {}
    if baseline_path.exists():
        with open(baseline_path, "r", encoding="utf-8") as f:
            result["baseline_benchmark"] = json.load(f)

    if dl_path.exists():
        with open(dl_path, "r", encoding="utf-8") as f:
            result["trained_deep_model_benchmark"] = json.load(f)

    # Combined summary
    if "baseline_benchmark" in result and "aggregate_track_metrics" in result["baseline_benchmark"]:
        result["aggregate_track_metrics"] = result["baseline_benchmark"]["aggregate_track_metrics"]
    if "baseline_benchmark" in result and "intensity_trend_metrics" in result["baseline_benchmark"]:
        result["intensity_trend_metrics"] = result["baseline_benchmark"]["intensity_trend_metrics"]

    return result

@router.get("/registry")
def get_model_registry():
    """Returns model versions, status (EVALUATED vs PENDING), and input/output contracts."""
    return {
        "models": [
            {
                "name": "DeepMultiHorizonTemporalNet",
                "version": "v1.0.0",
                "category": "TRACK_FORECAST",
                "status": "EVALUATED",
                "evaluated_mae_6h_km": 15.68,
                "evaluated_mae_24h_km": 58.43,
                "training_requirement": "STORM_SPLIT_TRAINED",
                "badge": "[TRAINED ACTIVE]"
            },
            {
                "name": "KinematicPersistenceBaseline",
                "version": "v1.0.0",
                "category": "TRACK_FORECAST",
                "status": "EVALUATED",
                "evaluated_mae_6h_km": 30.89,
                "evaluated_mae_24h_km": 141.22,
                "training_requirement": "ZERO_TRAINING_PHYSICS_BASELINE",
                "badge": "[BASELINE ACTIVE]"
            },
            {
                "name": "PhysicalPressureTrendBaseline",
                "version": "v1.0.0",
                "category": "INTENSITY_TREND",
                "status": "EVALUATED",
                "accuracy": 0.5988,
                "f1_score": 0.5210,
                "badge": "[BASELINE ACTIVE]"
            },
            {
                "name": "DeepIntensityClassifier",
                "version": "v1.0.0-rc",
                "category": "INTENSITY_TREND",
                "status": "MODEL_PENDING",
                "badge": "[MODEL PENDING (Baseline Active)]"
            },
            {
                "name": "CycloneEvolutionFingerprintExtractor",
                "version": "v1.0.0",
                "category": "STRUCTURAL_ORGANIZATION",
                "status": "EVALUATED",
                "badge": "[ALGORITHMIC ACTIVE]"
            }
        ]
    }
