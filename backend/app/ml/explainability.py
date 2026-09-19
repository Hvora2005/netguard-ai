"""Model explanations, with a documented fallback chain.

Preferred: SHAP (TreeExplainer) for tree-based models, when the optional
`shap` package is installed (see requirements-explainability.txt).

Fallback, when SHAP is unavailable or the model type isn't tree-based:
  - Tree/ensemble/boosting models -> the model's own feature_importances_
  - Linear models (logistic regression, linear-kernel SVM) -> coefficient x
    transformed feature value, a real per-instance contribution
  - Anything else (KNN, MLP, non-linear SVM without SHAP) -> unavailable,
    reported honestly rather than faked.

None of these values are causal explanations — they describe how much each
feature moved this particular model's output, not real-world causation.
"""

import numpy as np

from app.ml.registry import ModelBundle

TREE_MODEL_TYPES = {"random_forest", "decision_tree", "xgboost"}

try:
    import shap

    SHAP_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only when shap isn't installed
    SHAP_AVAILABLE = False

TOP_K = 10


def _feature_names(bundle: ModelBundle) -> list[str]:
    return list(bundle.preprocessor.get_feature_names_out())


def global_feature_importance(bundle: ModelBundle) -> tuple[list[dict] | None, str]:
    estimator = bundle.estimator
    feature_names = _feature_names(bundle)

    if hasattr(estimator, "feature_importances_"):
        importances = np.asarray(estimator.feature_importances_)
        method = "model_feature_importance"
    elif hasattr(estimator, "coef_"):
        coef = np.asarray(estimator.coef_)
        importances = np.abs(coef).mean(axis=0) if coef.ndim > 1 else np.abs(coef)
        method = "model_coefficients"
    else:
        return None, "unavailable"

    pairs = sorted(zip(feature_names, importances, strict=True), key=lambda item: -abs(item[1]))
    return [{"feature": f, "importance": float(v)} for f, v in pairs[:TOP_K]], method


def local_explanation(bundle: ModelBundle, x_transformed_row: np.ndarray, predicted_class_index: int) -> tuple[list[dict] | None, str]:
    estimator = bundle.estimator
    feature_names = _feature_names(bundle)
    row = np.asarray(x_transformed_row).reshape(1, -1)

    if SHAP_AVAILABLE and bundle.model_type in TREE_MODEL_TYPES:
        try:
            explainer = shap.TreeExplainer(estimator)
            shap_values = explainer.shap_values(row)
            if isinstance(shap_values, list):
                values = shap_values[predicted_class_index][0]
            else:
                values = shap_values[0]
                # Multiclass TreeExplainer output can be (1, n_features, n_classes)
                if values.ndim == 2:
                    values = values[:, predicted_class_index]
            pairs = sorted(zip(feature_names, values, strict=True), key=lambda item: -abs(item[1]))
            return [{"feature": f, "contribution": float(v)} for f, v in pairs[:TOP_K]], "shap"
        except Exception:
            pass  # fall through to the documented fallback below

    if hasattr(estimator, "coef_"):
        coef = np.asarray(estimator.coef_)
        class_coef = coef[predicted_class_index] if coef.ndim > 1 else coef
        contributions = class_coef * row[0]
        pairs = sorted(zip(feature_names, contributions, strict=True), key=lambda item: -abs(item[1]))
        return [{"feature": f, "contribution": float(v)} for f, v in pairs[:TOP_K]], "coefficient_contribution"

    if hasattr(estimator, "feature_importances_"):
        importances, _ = global_feature_importance(bundle)
        normalized = [{"feature": item["feature"], "contribution": item["importance"]} for item in (importances or [])]
        return normalized, "model_feature_importance_global_fallback"

    return None, "unavailable"
