from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.traffic import PcapAnalyzeResponse
from app.services import pcap_service, prediction_service

router = APIRouter(prefix="/pcap", tags=["pcap"])


@router.post("/analyze", response_model=PcapAnalyzeResponse)
async def analyze_pcap(
    file: UploadFile = File(...),
    model_id: int | None = Form(default=None),
    db: Session = Depends(get_db),
):
    content = await file.read()
    file_path = pcap_service.save_pcap_upload(file.filename, content)
    model = prediction_service.resolve_model(db, model_id)
    return pcap_service.analyze_pcap(db, file_path, file.filename, model)
