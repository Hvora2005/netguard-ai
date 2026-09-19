from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.prediction import ExplanationItem


class TrafficFlowSummary(BaseModel):
    id: int
    source_name: str
    src_ip: str
    dst_ip: str
    src_port: int | None
    dst_port: int | None
    protocol: str
    packet_count: int
    byte_count: int
    predicted_class: str | None
    confidence: float | None
    severity: str
    first_seen: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrafficFlowDetail(TrafficFlowSummary):
    duration_seconds: float
    packet_rate: float
    byte_rate: float
    model_id: int | None
    explanation: list[ExplanationItem] | None
    explanation_method: str | None


class TrafficFlowPage(BaseModel):
    items: list[TrafficFlowSummary]
    total: int
    page: int
    page_size: int


class PcapAnalyzeResponse(BaseModel):
    flow_count: int
    alerts_created: int
    classification_breakdown: dict[str, int]
    model_used: str
