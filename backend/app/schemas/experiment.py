from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.preprocessing import PreprocessingConfig


class TrainRequest(BaseModel):
    dataset_id: int
    model_type: str
    model_name: str | None = None
    hyperparameters: dict = {}
    preprocessing: PreprocessingConfig


class ExperimentSummary(BaseModel):
    id: int
    dataset_id: int
    model_type: str
    task_type: str
    status: str
    error_message: str | None
    duration_seconds: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperimentDetail(ExperimentSummary):
    preprocessing_config: dict
    hyperparameters: dict
    metrics: dict | None
    feature_names: list[str] | None
    class_labels: list[str] | None
