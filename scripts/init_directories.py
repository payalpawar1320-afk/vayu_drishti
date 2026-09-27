import os
from pathlib import Path

DIRECTORIES = [
    "configs",
    "data/raw/ibtracs",
    "data/raw/hursat_b1",
    "data/raw/hursat_avhrr",
    "data/raw/era5",
    "data/raw/gis",
    "data/processed/aligned_observations",
    "data/processed/sequences",
    "data/processed/gis_cache",
    "data/metadata",
    "backend/app/api/v1",
    "backend/app/core",
    "backend/app/providers",
    "backend/app/schemas",
    "ml/preprocessing",
    "ml/detection",
    "ml/classification",
    "ml/evolution",
    "ml/track_prediction",
    "ml/intensity",
    "ml/explainability",
    "ml/evaluation",
    "gis/corridor",
    "gis/intersection",
    "gis/population",
    "gis/infrastructure",
    "gis/scenario",
    "models/baseline",
    "models/trained",
    "experiments/splits",
    "experiments/logs",
    "notebooks",
    "scripts",
    "tests",
]

def create_dirs(base_path: Path):
    for d in DIRECTORIES:
        target = base_path / d
        target.mkdir(parents=True, exist_ok=True)
        # Create __init__.py for python packages
        if any(d.startswith(prefix) for prefix in ["backend", "ml", "gis", "tests"]):
            init_file = target / "__init__.py"
            if not init_file.exists():
                init_file.write_text("# Package init\n", encoding="utf-8")
        print(f"Created: {d}")

if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    create_dirs(base)
    print("All project directories successfully initialized.")
