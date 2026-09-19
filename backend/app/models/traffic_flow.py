from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TrafficFlow(Base):
    __tablename__ = "traffic_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_name: Mapped[str] = mapped_column(String, nullable=False)  # originating pcap filename
    model_id: Mapped[int | None] = mapped_column(ForeignKey("ml_models.id"), nullable=True)

    src_ip: Mapped[str] = mapped_column(String, nullable=False)
    dst_ip: Mapped[str] = mapped_column(String, nullable=False)
    src_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dst_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protocol: Mapped[str] = mapped_column(String, nullable=False)

    packet_count: Mapped[int] = mapped_column(Integer, default=0)
    byte_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0)
    packet_rate: Mapped[float] = mapped_column(Float, default=0)
    byte_rate: Mapped[float] = mapped_column(Float, default=0)
    syn_count: Mapped[int] = mapped_column(Integer, default=0)
    ack_count: Mapped[int] = mapped_column(Integer, default=0)

    predicted_class: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity: Mapped[str] = mapped_column(String, default="none")

    first_seen: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    model = relationship("MLModel")
