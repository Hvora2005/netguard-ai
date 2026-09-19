from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.alert import SecurityAlertPage, SecurityAlertSummary, UpdateAlertStatusRequest
from app.services import alert_service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=SecurityAlertPage)
def list_alerts(
    severity: str | None = None,
    status: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return alert_service.list_alerts(db, severity=severity, status=status, page=page, page_size=page_size)


@router.put("/{alert_id}/status", response_model=SecurityAlertSummary)
def update_alert_status(alert_id: int, payload: UpdateAlertStatusRequest, db: Session = Depends(get_db)):
    alert = alert_service.get_alert_or_404(db, alert_id)
    return alert_service.update_status(db, alert, payload.status)
