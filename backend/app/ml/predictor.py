import numpy as np
import pandas as pd

from app.ml.explainability import global_feature_importance, local_explanation
from app.ml.registry import ModelBundle
from app.utils.errors import AppError


def predict_single(bundle: ModelBundle, raw_features: dict) -> dict:
    row = {col: raw_features.get(col, np.nan) for col in bundle.feature_columns}
    df = pd.DataFrame([row], columns=bundle.feature_columns)

    try:
        transformed = bundle.preprocessor.transform(df)
    except Exception as exc:
        raise AppError(f"Could not transform the provided features: {exc}") from exc

    prediction_index = int(bundle.estimator.predict(transformed)[0])
    predicted_class = bundle.class_labels[prediction_index]

    probabilities = None
    confidence = None
    if hasattr(bundle.estimator, "predict_proba"):
        proba = bundle.estimator.predict_proba(transformed)[0]
        probabilities = {label: float(p) for label, p in zip(bundle.class_labels, proba, strict=True)}
        confidence = float(proba[prediction_index])

    explanation, explanation_method = local_explanation(bundle, transformed[0], prediction_index)

    return {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "probabilities": probabilities,
        "explanation": explanation,
        "explanation_method": explanation_method,
    }


def predict_batch(bundle: ModelBundle, df: pd.DataFrame) -> tuple[list[str], list[float | None]]:
    """Used by PCAP flow classification: predicts for every row of an already-aligned DataFrame."""
    for col in bundle.feature_columns:
        if col not in df.columns:
            df[col] = np.nan
    ordered = df[bundle.feature_columns]

    transformed = bundle.preprocessor.transform(ordered)
    predictions = bundle.estimator.predict(transformed)
    classes = [bundle.class_labels[int(i)] for i in predictions]

    confidences: list[float | None] = [None] * len(classes)
    if hasattr(bundle.estimator, "predict_proba"):
        proba = bundle.estimator.predict_proba(transformed)
        confidences = [float(proba[i, int(pred)]) for i, pred in enumerate(predictions)]

    return classes, confidences


def get_global_explanation(bundle: ModelBundle) -> dict:
    importances, method = global_feature_importance(bundle)
    return {"importances": importances, "method": method}
