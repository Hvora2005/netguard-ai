from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.dataset import Dataset
from app.services.demo_data import generate_demo_dataset
from app.preprocessing.inspection import (
    class_distribution,
    clean_column_names,
    column_metadata,
    guess_target_column,
    missing_value_summary,
    replace_inf_with_nan,
)
from app.utils.errors import AppError
from app.utils.files import sanitize_filename, unique_stored_name

MAX_PREVIEW_ROWS = 50


def load_dataframe(file_path: Path) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path, low_memory=False)
    except Exception as exc:  # pandas raises many different error types for malformed CSVs
        raise AppError(f"Could not parse CSV file: {exc}") from exc

    if df.empty or df.shape[1] == 0:
        raise AppError("The uploaded CSV is empty or has no columns.")

    df = clean_column_names(df)
    df = replace_inf_with_nan(df)
    return df


def save_upload(original_filename: str, content: bytes) -> Path:
    if not original_filename.lower().endswith(".csv"):
        raise AppError("Only .csv files are supported for dataset upload.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise AppError(f"File exceeds the {settings.max_upload_size_mb}MB upload limit.")

    upload_dir = settings.resolve_path(settings.upload_path)
    stored_name = unique_stored_name(sanitize_filename(original_filename))
    file_path = upload_dir / stored_name
    file_path.write_bytes(content)
    return file_path


def register_dataset(db: Session, original_filename: str, file_path: Path, is_demo: bool = False) -> Dataset:
    df = load_dataframe(file_path)

    target_column = guess_target_column(df)

    dataset = Dataset(
        filename=file_path.name,
        original_filename=sanitize_filename(original_filename),
        file_path=str(file_path),
        n_rows=int(df.shape[0]),
        n_columns=int(df.shape[1]),
        size_bytes=file_path.stat().st_size,
        target_column=target_column,
        columns_meta=column_metadata(df),
        class_distribution=class_distribution(df, target_column),
        missing_values=missing_value_summary(df),
        duplicate_rows=int(df.duplicated().sum()),
        is_demo=is_demo,
        status="ready",
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_dataset_or_404(db: Session, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise AppError(f"Dataset {dataset_id} was not found.", status_code=404)
    return dataset


def get_preview(dataset: Dataset) -> dict:
    df = load_dataframe(Path(dataset.file_path))
    preview_df = df.head(MAX_PREVIEW_ROWS).where(pd.notna(df.head(MAX_PREVIEW_ROWS)), None)
    return {
        "columns": list(df.columns),
        "rows": preview_df.to_dict(orient="records"),
    }


def generate_and_register_demo(db: Session) -> Dataset:
    upload_dir = settings.resolve_path(settings.upload_path)
    df = generate_demo_dataset()
    stored_name = unique_stored_name("demo_traffic.csv")
    file_path = upload_dir / stored_name
    df.to_csv(file_path, index=False)
    return register_dataset(db, "demo_traffic.csv", file_path, is_demo=True)


def set_target_column(db: Session, dataset: Dataset, target_column: str) -> Dataset:
    df = load_dataframe(Path(dataset.file_path))
    if target_column not in df.columns:
        raise AppError(f"Column '{target_column}' does not exist in this dataset.")

    dataset.target_column = target_column
    dataset.class_distribution = class_distribution(df, target_column)
    db.commit()
    db.refresh(dataset)
    return dataset
