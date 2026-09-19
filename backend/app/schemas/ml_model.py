from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MLModelSummary(BaseModel):
    id: int
    experiment_id: int
    name: str
    model_type: str
    task_type: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RenameModelRequest(BaseModel):
    name: str
