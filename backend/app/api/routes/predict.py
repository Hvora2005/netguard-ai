from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.prediction import (
    GlobalExplanationResponse,
    ModelFeatureSchema,
    PredictionRequest,
    PredictionResponse,
)
from app.services import prediction_service

router = APIRouter(tags=["prediction"])


@router.get("/models/{model_id}/feature-schema", response_model=ModelFeatureSchema)
def feature_schema(model_id: int, db: Session = Depends(get_db)):
    model = prediction_service.resolve_model(db, model_id)
    bundle = prediction_service.load_model_bundle(model)
    return prediction_service.build_feature_schema(model, bundle)


@router.get("/models/{model_id}/explain/global", response_model=GlobalExplanationResponse)
def global_explanation(model_id: int, db: Session = Depends(get_db)):
    model = prediction_service.resolve_model(db, model_id)
    return prediction_service.get_model_global_explanation(model)


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest, db: Session = Depends(get_db)):
    model = prediction_service.resolve_model(db, payload.model_id)
    return prediction_service.run_prediction(db, model, payload.features)
