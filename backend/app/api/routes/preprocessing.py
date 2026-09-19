from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.preprocessing import PreprocessingPreviewRequest, PreprocessingPreviewResponse
from app.services import dataset_service, preprocessing_service

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])


@router.post("/preview", response_model=PreprocessingPreviewResponse)
def preview(payload: PreprocessingPreviewRequest, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset_or_404(db, payload.dataset_id)
    return preprocessing_service.preview_preprocessing(dataset, payload.config)
