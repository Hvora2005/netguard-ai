from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GenerateReportRequest(BaseModel):
    experiment_id: int
    formats: list[str] = Field(default_factory=lambda: ["html"])


class ReportSummary(BaseModel):
    id: int
    experiment_id: int
    html_path: str | None
    csv_path: str | None
    pdf_path: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
