"""Persists a trained (preprocessor + model + metadata) bundle as a single
joblib file, so preprocessing fitted during training is always reused
consistently at prediction time instead of re-fit on new data.
"""

from dataclasses import dataclass
from pathlib import Path

import joblib

from app.core.config import settings


@dataclass
class ModelBundle:
    preprocessor: object
    estimator: object
    feature_columns: list[str]
    numeric_columns: list[str]
    categorical_columns: list[str]
    class_labels: list[str]
    task_type: str
    model_type: str


def save_bundle(bundle: ModelBundle, experiment_id: int) -> str:
    storage_dir = settings.resolve_path(settings.model_storage_path)
    path = storage_dir / f"experiment_{experiment_id}.joblib"
    joblib.dump(bundle, path)
    return str(path)


def load_bundle(bundle_path: str) -> ModelBundle:
    path = Path(bundle_path)
    if not path.exists():
        raise FileNotFoundError(f"Model bundle not found at {bundle_path}")
    return joblib.load(path)
