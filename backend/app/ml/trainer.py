import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.utils.class_weight import compute_class_weight
from sqlalchemy.orm import Session

from app.ml.evaluation import evaluate_predictions
from app.ml.model_factory import build_estimator, supports_class_weight
from app.ml.registry import ModelBundle, save_bundle
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.ml_model import MLModel
from app.preprocessing.pipeline import build_preprocessor, resolve_labels, split_feature_types
from app.schemas.experiment import TrainRequest
from app.services.dataset_service import load_dataframe
from app.utils.errors import AppError

try:
    from imblearn.over_sampling import SMOTE

    SMOTE_AVAILABLE = True
except ImportError:  # pragma: no cover
    SMOTE_AVAILABLE = False


def run_training(db: Session, dataset: Dataset, request: TrainRequest) -> Experiment:
    if not dataset.target_column:
        raise AppError("This dataset has no target column selected yet. Set one in the Dataset Explorer first.")

    config = request.preprocessing

    experiment = Experiment(
        dataset_id=dataset.id,
        model_type=request.model_type,
        task_type=config.task_type,
        preprocessing_config=config.model_dump(),
        hyperparameters=request.hyperparameters,
        status="running",
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    start = time.perf_counter()
    try:
        df = load_dataframe(Path(dataset.file_path))
        if dataset.target_column not in df.columns:
            raise AppError(f"Target column '{dataset.target_column}' no longer exists in this dataset.")

        feature_columns = config.feature_columns or [c for c in df.columns if c != dataset.target_column]
        missing = [c for c in feature_columns if c not in df.columns]
        if missing:
            raise AppError(f"Unknown feature columns: {', '.join(missing)}")

        if config.missing_strategy == "drop_rows":
            df = df.dropna(subset=feature_columns)

        labels = resolve_labels(df[dataset.target_column], config)
        if labels.nunique() < 2:
            raise AppError("The selected target only has one class after label mapping; classification requires at least two classes.")

        numeric_cols, categorical_cols = split_feature_types(df, feature_columns)

        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(labels)
        class_labels = list(label_encoder.classes_)

        X_train, X_test, y_train, y_test = train_test_split(
            df[feature_columns],
            y_encoded,
            test_size=config.test_size,
            random_state=config.random_state,
            stratify=y_encoded,
        )

        # Preprocessing is fit ONLY on the training split, then applied to both
        # splits, so no information about the test set leaks into training.
        preprocessor = build_preprocessor(config, numeric_cols, categorical_cols)
        X_train_transformed = preprocessor.fit_transform(X_train)
        X_test_transformed = preprocessor.transform(X_test)

        class_weight = None
        if config.handle_imbalance == "class_weight":
            if supports_class_weight(request.model_type):
                weights = compute_class_weight("balanced", classes=np.unique(y_train), y=y_train)
                class_weight = {cls: w for cls, w in zip(np.unique(y_train), weights, strict=True)}
            else:
                pass  # noted below via metrics warning; model_factory silently ignores class_weight for unsupported models

        if config.handle_imbalance == "smote":
            if not SMOTE_AVAILABLE:
                raise AppError("SMOTE was requested but the 'imbalanced-learn' package is not installed on the server.")
            min_class_count = int(np.bincount(y_train).min())
            if min_class_count < 2:
                raise AppError("SMOTE requires at least 2 training samples in every class.")
            k_neighbors = max(1, min(5, min_class_count - 1))
            smote = SMOTE(random_state=config.random_state, k_neighbors=k_neighbors)
            X_train_transformed, y_train = smote.fit_resample(X_train_transformed, y_train)

        estimator = build_estimator(request.model_type, request.hyperparameters, class_weight, config.random_state)
        estimator.fit(X_train_transformed, y_train)

        y_pred = estimator.predict(X_test_transformed)
        y_proba = estimator.predict_proba(X_test_transformed) if hasattr(estimator, "predict_proba") else None

        metrics = evaluate_predictions(y_test, y_pred, y_proba, class_labels)

        duration = time.perf_counter() - start

        bundle = ModelBundle(
            preprocessor=preprocessor,
            estimator=estimator,
            feature_columns=feature_columns,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            class_labels=class_labels,
            task_type=config.task_type,
            model_type=request.model_type,
        )
        bundle_path = save_bundle(bundle, experiment.id)

        experiment.metrics = metrics
        experiment.feature_names = feature_columns
        experiment.class_labels = class_labels
        experiment.status = "completed"
        experiment.duration_seconds = duration
        db.commit()

        model_record = MLModel(
            experiment_id=experiment.id,
            name=request.model_name or f"{request.model_type}-{experiment.id}",
            model_type=request.model_type,
            task_type=config.task_type,
            bundle_path=bundle_path,
            is_active=False,
        )
        db.add(model_record)
        db.commit()

        db.refresh(experiment)
        return experiment

    except AppError as exc:
        experiment.status = "failed"
        experiment.error_message = exc.message
        db.commit()
        raise
    except Exception as exc:  # noqa: BLE001 - convert unexpected training failures into a clean, stored error
        experiment.status = "failed"
        experiment.error_message = f"Training failed: {exc}"
        db.commit()
        raise AppError(f"Training failed: {exc}") from exc
