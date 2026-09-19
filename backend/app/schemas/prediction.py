from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeatureSchemaField(BaseModel):
    name: str
    is_numeric: bool


class ModelFeatureSchema(BaseModel):
    model_id: int
    model_name: str
    task_type: str
    class_labels: list[str]
    fields: list[FeatureSchemaField]


class PredictionRequest(BaseModel):
    model_id: int | None = None  # None => use the active model
    features: dict


class ExplanationItem(BaseModel):
    feature: str
    contribution: float


class PredictionResponse(BaseModel):
    id: int
    model_id: int
    predicted_class: str
    confidence: float | None
    probabilities: dict[str, float] | None
    explanation: list[ExplanationItem] | None
    explanation_method: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GlobalExplanationItem(BaseModel):
    feature: str
    importance: float


class GlobalExplanationResponse(BaseModel):
    model_id: int
    method: str
    importances: list[GlobalExplanationItem] | None
