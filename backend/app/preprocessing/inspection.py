"""Dataset inspection helpers: pure functions over a pandas DataFrame.

These are used right after a CSV upload to compute the metadata shown in the
Dataset Explorer, and are intentionally side-effect free so they can also be
reused by tests.
"""

import numpy as np
import pandas as pd

LIKELY_TARGET_NAMES = [
    "label",
    "labels",
    "class",
    "attack_cat",
    "attack",
    "category",
    "target",
]


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    return df


def guess_target_column(df: pd.DataFrame) -> str | None:
    lowered = {c: c.lower() for c in df.columns}
    for candidate in LIKELY_TARGET_NAMES:
        for original, low in lowered.items():
            if low == candidate:
                return original
    for candidate in LIKELY_TARGET_NAMES:
        for original, low in lowered.items():
            if candidate in low:
                return original
    return None


def column_metadata(df: pd.DataFrame) -> list[dict]:
    meta = []
    for col in df.columns:
        series = df[col]
        is_numeric = pd.api.types.is_numeric_dtype(series)
        meta.append(
            {
                "name": col,
                "dtype": str(series.dtype),
                "is_numeric": bool(is_numeric),
                "missing_count": int(series.isna().sum()),
                "unique_count": int(series.nunique(dropna=True)),
            }
        )
    return meta


def missing_value_summary(df: pd.DataFrame) -> dict[str, int]:
    counts = df.isna().sum()
    return {col: int(v) for col, v in counts.items() if v > 0}


def class_distribution(df: pd.DataFrame, target_column: str | None) -> dict[str, int] | None:
    if not target_column or target_column not in df.columns:
        return None
    counts = df[target_column].astype(str).value_counts()
    return {str(k): int(v) for k, v in counts.items()}


def replace_inf_with_nan(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].replace([np.inf, -np.inf], np.nan)
    return df
