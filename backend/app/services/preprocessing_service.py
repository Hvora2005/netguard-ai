from pathlib import Path

import pandas as pd

from app.models.dataset import Dataset
from app.preprocessing.pipeline import build_preprocessor, numeric_stats, resolve_labels, split_feature_types
from app.schemas.preprocessing import PreprocessingConfig
from app.services.dataset_service import load_dataframe
from app.utils.errors import AppError

try:
    from imblearn.over_sampling import SMOTE

    SMOTE_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when imbalanced-learn isn't installed
    SMOTE_AVAILABLE = False


def preview_preprocessing(dataset: Dataset, config: PreprocessingConfig) -> dict:
    if not dataset.target_column:
        raise AppError("This dataset has no target column selected yet. Set one in the Dataset Explorer first.")

    df = load_dataframe(Path(dataset.file_path))
    if dataset.target_column not in df.columns:
        raise AppError(f"Target column '{dataset.target_column}' no longer exists in this dataset.")

    feature_columns = config.feature_columns or [c for c in df.columns if c != dataset.target_column]
    missing = [c for c in feature_columns if c not in df.columns]
    if missing:
        raise AppError(f"Unknown feature columns: {', '.join(missing)}")

    notes: list[str] = []

    working = df.copy()
    if config.missing_strategy == "drop_rows":
        before_rows = len(working)
        working = working.dropna(subset=feature_columns)
        notes.append(f"Dropped {before_rows - len(working)} rows containing missing values.")

    labels_before = resolve_labels(working[dataset.target_column], config)
    before_distribution = labels_before.value_counts().to_dict()

    numeric_cols, categorical_cols = split_feature_types(working, feature_columns)
    before_stats = numeric_stats(working, numeric_cols)

    preprocessor = build_preprocessor(config, numeric_cols, categorical_cols)
    transformed = preprocessor.fit_transform(working[feature_columns])

    feature_names = list(preprocessor.get_feature_names_out())
    after_df = pd.DataFrame(transformed, columns=feature_names)
    numeric_after_cols = [c for c in feature_names if c.startswith("numeric__")]
    after_stats = numeric_stats(after_df, numeric_after_cols)

    labels_after = labels_before.reset_index(drop=True)
    after_distribution = dict(before_distribution)

    if config.handle_imbalance == "smote":
        if not SMOTE_AVAILABLE:
            notes.append("SMOTE was requested but the 'imbalanced-learn' package is not installed; showing original class balance instead.")
        else:
            min_class_count = labels_after.value_counts().min()
            k_neighbors = max(1, min(5, min_class_count - 1))
            if min_class_count < 2:
                notes.append("SMOTE requires at least 2 samples per class; skipping oversampling preview for this dataset.")
            else:
                smote = SMOTE(random_state=config.random_state, k_neighbors=k_neighbors)
                _, resampled_labels = smote.fit_resample(transformed, labels_after)
                after_distribution = resampled_labels.value_counts().to_dict()
                notes.append("Preview shows the effect of SMOTE oversampling on the training class balance.")
    elif config.handle_imbalance == "class_weight":
        notes.append("Class weights will be passed to the model during training instead of resampling the data.")

    notes.append(
        "This preview fits preprocessing on the FULL dataset purely for illustration. "
        "Actual training fits preprocessing only on the training split to avoid data leakage."
    )

    return {
        "before_row_count": int(len(df)),
        "after_row_count": int(len(working)),
        "before_class_distribution": {str(k): int(v) for k, v in before_distribution.items()},
        "after_class_distribution": {str(k): int(v) for k, v in after_distribution.items()},
        "before_numeric_stats": before_stats,
        "after_numeric_stats": after_stats,
        "numeric_feature_count": len(numeric_cols),
        "categorical_feature_count": len(categorical_cols),
        "notes": notes,
    }
