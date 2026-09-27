import json
import random
from pathlib import Path
from typing import Dict, Any, List

from backend.app.providers.ibtracs_provider import IBTrACSProvider

SPLITS_FILE = Path(__file__).resolve().parent.parent.parent / "experiments" / "splits" / "storm_splits.json"

# Fixed benchmark test storms to prevent temporal leakage per Section 41 of SPEC.md
DESIGNATED_TEST_STORMS = ["AMPHAN", "FANI", "TAUKTAE"]
DESIGNATED_VAL_STORMS = ["BIPARJOY", "YAAS", "HUDHUD", "PHAILIN", "TITLI"]

def generate_storm_splits(seed: int = 42) -> Dict[str, Any]:
    print("[StormSplits] Generating strict storm-level non-overlapping splits...")
    provider = IBTrACSProvider()
    all_storms = provider.get_storms(basin="NI")

    # Filter for storms with sufficient observations for temporal sequences (>= 12 points)
    viable_storms = [s for s in all_storms if s.total_observations >= 12]
    print(f"[StormSplits] Total viable named storms (>= 12 points): {len(viable_storms)}")

    test_set = []
    val_set = []
    train_set = []

    viable_names = {s.storm_name: s for s in viable_storms}

    # 1. Assign Test Storms
    for name in DESIGNATED_TEST_STORMS:
        if name in viable_names:
            s = viable_names.pop(name)
            test_set.append({"storm_id": s.storm_id, "storm_name": s.storm_name, "year": s.year, "points": s.total_observations})

    # 2. Assign Val Storms
    for name in DESIGNATED_VAL_STORMS:
        if name in viable_names:
            s = viable_names.pop(name)
            val_set.append({"storm_id": s.storm_id, "storm_name": s.storm_name, "year": s.year, "points": s.total_observations})

    # 3. Assign remaining viable storms to Train (and random partition if needed)
    remaining = list(viable_names.values())
    random.seed(seed)
    random.shuffle(remaining)

    for s in remaining:
        train_set.append({"storm_id": s.storm_id, "storm_name": s.storm_name, "year": s.year, "points": s.total_observations})

    splits_data = {
        "split_strategy": "STORM_LEVEL_TEMPORAL_ISOLATION (ZERO_LEAKAGE)",
        "citation": "Section 41 of SPEC.md",
        "train_count": len(train_set),
        "val_count": len(val_set),
        "test_count": len(test_set),
        "train_storms": train_set,
        "val_storms": val_set,
        "test_storms": test_set
    }

    SPLITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SPLITS_FILE, "w", encoding="utf-8") as f:
        json.dump(splits_data, f, indent=2)

    print(f"[StormSplits] Successfully saved splits to {SPLITS_FILE}:")
    print(f"  Train: {len(train_set)} storms | Val: {len(val_set)} storms | Test: {len(test_set)} storms")
    return splits_data

if __name__ == "__main__":
    generate_storm_splits()
