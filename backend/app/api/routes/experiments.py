from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.experiment import Experiment
from app.schemas.experiment import ExperimentDetail, ExperimentSummary
from app.utils.errors import AppError

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=list[ExperimentSummary])
def list_experiments(db: Session = Depends(get_db)):
    return db.execute(select(Experiment).order_by(Experiment.created_at.desc())).scalars().all()


@router.get("/{experiment_id}", response_model=ExperimentDetail)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise AppError(f"Experiment {experiment_id} was not found.", status_code=404)
    return experiment
