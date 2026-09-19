from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ml.predictor import get_global_explanation, predict_single
from app.ml.registry import ModelBundle, load_bundle
from app.models.ml_model import MLModel
from app.models.prediction import Prediction
from app.utils.errors import AppError


def resolve_model(db: Session, model_id: int | None) -> MLModel:
    if model_id is not None:
        model = db.get(MLModel, model_id)
        if model is None:
            raise AppError(f"Model {model_id} was not found.", status_code=404)
        return model

    model = db.execute(select(MLModel).where(MLModel.is_active.is_(True))).scalars().first()
    if model is None:
        raise AppError("No model_id was given and no model is currently marked active. Activate one in Model Comparison first.")
    return model


def load_model_bundle(model: MLModel) -> ModelBundle:
    try:
        return load_bundle(model.bundle_path)
    except FileNotFoundError as exc:
        raise AppError(f"The saved model file for '{model.name}' is missing on disk.", status_code=404) from exc


def build_feature_schema(model: MLModel, bundle: ModelBundle) -> dict:
    numeric_set = set(bundle.numeric_columns)
    fields = [{"name": col, "is_numeric": col in numeric_set} for col in bundle.feature_columns]
    return {
        "model_id": model.id,
        "model_name": model.name,
        "task_type": bundle.task_type,
        "class_labels": bundle.class_labels,
        "fields": fields,
    }


def run_prediction(db: Session, model: MLModel, features: dict) -> Prediction:
    bundle = load_model_bundle(model)
    result = predict_single(bundle, features)

    record = Prediction(
        model_id=model.id,
        input_features=features,
        predicted_class=result["predicted_class"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        explanation=result["explanation"],
        explanation_method=result["explanation_method"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_model_global_explanation(model: MLModel) -> dict:
    bundle = load_model_bundle(model)
    explanation = get_global_explanation(bundle)
    return {"model_id": model.id, **explanation}
