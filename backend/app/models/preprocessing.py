from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from typing import Optional, Any
from app.models.base import UUIDBaseModel
import uuid


class PreprocessingReport(UUIDBaseModel):
    __tablename__ = "preprocessing_reports"

    dataset_id:     Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), nullable=False, index=True)
    status:         Mapped[str]       = mapped_column(String(50), default="pending")
    input_shape:    Mapped[Optional[list[int]]]  = mapped_column(JSONB, nullable=True)
    output_shape:   Mapped[Optional[list[int]]]  = mapped_column(JSONB, nullable=True)
    output_columns: Mapped[Optional[list[str]]]  = mapped_column(JSONB, nullable=True)
    pipeline_path:  Mapped[Optional[str]]        = mapped_column(String(1024), nullable=True)
    report:         Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    error_message:  Mapped[Optional[str]]        = mapped_column(String(2048), nullable=True)

    dataset: Mapped["Dataset"] = relationship("Dataset", foreign_keys=[dataset_id])  # type: ignore[name-defined]
