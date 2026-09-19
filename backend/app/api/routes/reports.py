from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.experiment import Experiment
from app.models.report import Report
from app.schemas.report import GenerateReportRequest, ReportSummary
from app.services import report_service
from app.utils.errors import AppError

router = APIRouter(prefix="/reports", tags=["reports"])

MEDIA_TYPES = {"html": "text/html", "csv": "text/csv", "pdf": "application/pdf"}


@router.post("/generate", response_model=ReportSummary)
def generate_report(payload: GenerateReportRequest, db: Session = Depends(get_db)):
    experiment = db.get(Experiment, payload.experiment_id)
    if experiment is None:
        raise AppError(f"Experiment {payload.experiment_id} was not found.", status_code=404)
    return report_service.generate_report(db, experiment, payload.formats)


@router.get("", response_model=list[ReportSummary])
def list_reports(db: Session = Depends(get_db)):
    return db.execute(select(Report).order_by(Report.created_at.desc())).scalars().all()


@router.get("/{report_id}/download")
def download_report(report_id: int, format: str = "html", db: Session = Depends(get_db)):
    report = report_service.get_report_or_404(db, report_id)
    path = report_service.resolve_report_file(report, format)
    return FileResponse(path, media_type=MEDIA_TYPES.get(format, "application/octet-stream"), filename=path.name)
