from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.traffic import TrafficFlowDetail, TrafficFlowPage
from app.services import traffic_service

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.get("", response_model=TrafficFlowPage)
def list_traffic(
    predicted_class: str | None = None,
    protocol: str | None = None,
    severity: str | None = None,
    src_ip: str | None = None,
    dst_ip: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return traffic_service.list_flows(
        db,
        predicted_class=predicted_class,
        protocol=protocol,
        severity=severity,
        src_ip=src_ip,
        dst_ip=dst_ip,
        start=start,
        end=end,
        page=page,
        page_size=page_size,
    )


@router.get("/{flow_id}", response_model=TrafficFlowDetail)
def get_flow(flow_id: int, db: Session = Depends(get_db)):
    return traffic_service.get_flow_with_explanation(db, flow_id)
