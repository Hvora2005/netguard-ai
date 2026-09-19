from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetDetail, DatasetPreview, DatasetSummary, SetTargetColumnRequest
from app.services import dataset_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetDetail)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    file_path = dataset_service.save_upload(file.filename, content)
    dataset = dataset_service.register_dataset(db, file.filename, file_path)
    return dataset


@router.post("/demo", response_model=DatasetDetail)
def load_demo_dataset(db: Session = Depends(get_db)):
    return dataset_service.generate_and_register_demo(db)


@router.get("", response_model=list[DatasetSummary])
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.execute(select(Dataset).order_by(Dataset.created_at.desc())).scalars().all()
    return datasets


@router.get("/{dataset_id}", response_model=DatasetDetail)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    return dataset_service.get_dataset_or_404(db, dataset_id)


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
def preview_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset_or_404(db, dataset_id)
    return dataset_service.get_preview(dataset)


@router.put("/{dataset_id}/target-column", response_model=DatasetDetail)
def update_target_column(dataset_id: int, payload: SetTargetColumnRequest, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset_or_404(db, dataset_id)
    return dataset_service.set_target_column(db, dataset, payload.target_column)


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset_or_404(db, dataset_id)
    db.delete(dataset)
    db.commit()
    return {"status": "deleted", "id": dataset_id}
