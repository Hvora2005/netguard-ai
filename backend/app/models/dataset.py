from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_path: Mapped[str] = mapped_column(String, nullable=False)

    n_rows: Mapped[int] = mapped_column(Integer, default=0)
    n_columns: Mapped[int] = mapped_column(Integer, default=0)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    target_column: Mapped[str | None] = mapped_column(String, nullable=True)

    # JSON blobs holding derived metadata computed once at upload time.
    columns_meta: Mapped[list | None] = mapped_column(JSON, nullable=True)
    class_distribution: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    missing_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    duplicate_rows: Mapped[int] = mapped_column(Integer, default=0)

    is_demo: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(String, default="ready")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
