from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.experiment import ExperimentDetail, TrainRequest
from app.schemas.ml_model import MLModelSummary, RenameModelRequest
from app.services import dataset_service, model_service
from app.ml.trainer import run_training

router = APIRouter(tags=["models"])


@router.post("/models/train", response_model=ExperimentDetail)
def train_model(payload: TrainRequest, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset_or_404(db, payload.dataset_id)
    experiment = run_training(db, dataset, payload)
    return experiment


@router.get("/models", response_model=list[MLModelSummary])
def list_models(db: Session = Depends(get_db)):
    return model_service.list_models(db)


@router.get("/models/{model_id}", response_model=MLModelSummary)
def get_model(model_id: int, db: Session = Depends(get_db)):
    return model_service.get_model_or_404(db, model_id)


@router.put("/models/{model_id}/rename", response_model=MLModelSummary)
def rename_model(model_id: int, payload: RenameModelRequest, db: Session = Depends(get_db)):
    model = model_service.get_model_or_404(db, model_id)
    return model_service.rename_model(db, model, payload.name)


@router.put("/models/{model_id}/activate", response_model=MLModelSummary)
def activate_model(model_id: int, db: Session = Depends(get_db)):
    model = model_service.get_model_or_404(db, model_id)
    return model_service.set_active_model(db, model)


@router.delete("/models/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    model = model_service.get_model_or_404(db, model_id)
    model_service.delete_model(db, model)
    return {"status": "deleted", "id": model_id}
