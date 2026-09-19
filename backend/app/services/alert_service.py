from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.security_alert import SecurityAlert
from app.utils.errors import AppError


def list_alerts(db: Session, *, severity: str | None = None, status: str | None = None, page: int = 1, page_size: int = 25) -> dict:
    query = select(SecurityAlert)
    if severity:
        query = query.where(SecurityAlert.severity == severity)
    if status:
        query = query.where(SecurityAlert.status == status)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()

    page = max(page, 1)
    page_size = min(max(page_size, 1), 200)
    items = (
        db.execute(query.order_by(SecurityAlert.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
        .scalars()
        .all()
    )

    return {"items": items, "total": total, "page": page, "page_size": page_size}


def get_alert_or_404(db: Session, alert_id: int) -> SecurityAlert:
    alert = db.get(SecurityAlert, alert_id)
    if alert is None:
        raise AppError(f"Alert {alert_id} was not found.", status_code=404)
    return alert


def update_status(db: Session, alert: SecurityAlert, status: str) -> SecurityAlert:
    alert.status = status
    db.commit()
    db.refresh(alert)
    return alert
