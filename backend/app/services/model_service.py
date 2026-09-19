from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml_model import MLModel
from app.utils.errors import AppError


def list_models(db: Session) -> list[MLModel]:
    return db.execute(select(MLModel).order_by(MLModel.created_at.desc())).scalars().all()


def get_model_or_404(db: Session, model_id: int) -> MLModel:
    model = db.get(MLModel, model_id)
    if model is None:
        raise AppError(f"Model {model_id} was not found.", status_code=404)
    return model


def rename_model(db: Session, model: MLModel, name: str) -> MLModel:
    model.name = name
    db.commit()
    db.refresh(model)
    return model


def set_active_model(db: Session, model: MLModel) -> MLModel:
    db.query(MLModel).filter(MLModel.id != model.id).update({MLModel.is_active: False})
    model.is_active = True
    db.commit()
    db.refresh(model)
    return model


def delete_model(db: Session, model: MLModel) -> None:
    bundle_path = Path(model.bundle_path)
    if bundle_path.exists():
        bundle_path.unlink()
    db.delete(model)
    db.commit()
