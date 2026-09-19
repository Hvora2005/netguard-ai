from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SecurityAlertSummary(BaseModel):
    id: int
    flow_id: int
    severity: str
    classification: str
    confidence: float | None
    message: str
    source: str
    destination: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityAlertPage(BaseModel):
    items: list[SecurityAlertSummary]
    total: int
    page: int
    page_size: int


class UpdateAlertStatusRequest(BaseModel):
    status: str = Field(pattern="^(open|acknowledged|resolved)$")
