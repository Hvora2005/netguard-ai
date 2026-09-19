"""Builds the scikit-learn preprocessing pipeline from a PreprocessingConfig.

Critically, the returned ColumnTransformer is UNFITTED. Callers are
responsible for calling .fit(X_train) only on the training split and then
.transform() on both splits, so no information from the test set (including
its mean/variance used for scaling, or its categories used for encoding)
leaks into training. This is what app/ml/trainer.py does; app/api/routes/
preprocessing.py's "preview" endpoint fits on the whole dataset ONLY to show
the user an illustrative before/after comparison, and that fitted instance is
discarded rather than reused for real training.
"""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder, OrdinalEncoder, StandardScaler

from app.schemas.preprocessing import PreprocessingConfig


def split_feature_types(df: pd.DataFrame, feature_columns: list[str]) -> tuple[list[str], list[str]]:
    numeric_cols = [c for c in feature_columns if pd.api.types.is_numeric_dtype(df[c])]
    categorical_cols = [c for c in feature_columns if c not in numeric_cols]
    return numeric_cols, categorical_cols


def build_preprocessor(config: PreprocessingConfig, numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    numeric_steps = [("imputer", SimpleImputer(strategy=config.missing_strategy if config.missing_strategy != "drop_rows" else "median"))]
    if config.scaling == "standard":
        numeric_steps.append(("scaler", StandardScaler()))
    elif config.scaling == "minmax":
        numeric_steps.append(("scaler", MinMaxScaler()))
    numeric_pipeline = Pipeline(numeric_steps)

    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False)
                if config.categorical_encoding == "onehot"
                else OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
            ),
        ]
    )

    transformers = []
    if numeric_cols:
        transformers.append(("numeric", numeric_pipeline, numeric_cols))
    if categorical_cols:
        transformers.append(("categorical", categorical_pipeline, categorical_cols))

    return ColumnTransformer(transformers=transformers, remainder="drop")


def map_binary_labels(labels: pd.Series, benign_labels: list[str]) -> pd.Series:
    benign_set = {str(v).strip().lower() for v in benign_labels}
    return labels.astype(str).str.strip().apply(lambda v: "BENIGN" if v.lower() in benign_set else "MALICIOUS")


def resolve_labels(labels: pd.Series, config: PreprocessingConfig) -> pd.Series:
    if config.task_type == "binary":
        return map_binary_labels(labels, config.benign_labels)
    return labels.astype(str).str.strip()


def numeric_stats(df: pd.DataFrame, numeric_cols: list[str]) -> list[dict]:
    stats = []
    for col in numeric_cols:
        series = df[col]
        stats.append(
            {
                "name": col,
                "mean": None if series.dropna().empty else float(np.mean(series.dropna())),
                "std": None if series.dropna().empty else float(np.std(series.dropna())),
                "missing_count": int(series.isna().sum()),
            }
        )
    return stats
