from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ColumnMeta(BaseModel):
    name: str
    dtype: str
    is_numeric: bool
    missing_count: int
    unique_count: int


class DatasetSummary(BaseModel):
    id: int
    filename: str
    original_filename: str
    n_rows: int
    n_columns: int
    size_bytes: int
    target_column: str | None
    is_demo: bool
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetDetail(DatasetSummary):
    columns_meta: list[ColumnMeta] | None
    class_distribution: dict[str, int] | None
    missing_values: dict[str, int] | None
    duplicate_rows: int


class DatasetPreview(BaseModel):
    columns: list[str]
    rows: list[dict]


class SetTargetColumnRequest(BaseModel):
    target_column: str
