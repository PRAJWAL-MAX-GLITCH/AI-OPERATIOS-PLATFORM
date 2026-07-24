from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from typing import Optional, Any
from app.models.base import UUIDBaseModel
import uuid


class TrainingJob(UUIDBaseModel):
    __tablename__ = "training_jobs"

    dataset_id:    Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), nullable=False, index=True)
    project_id:    Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    status:        Mapped[str]       = mapped_column(String(50), default="pending")  # pending|running|completed|failed
    algorithm:     Mapped[str]       = mapped_column(String(100), nullable=False)
    problem_type:  Mapped[str]       = mapped_column(String(50), nullable=False)     # classification|regression|clustering
    target_column: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    metrics:       Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    parameters:    Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    model_path:    Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    
    # Store the preprocessing pipeline path to recreate features during inference
    preprocessing_pipeline_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    dataset: Mapped["Dataset"] = relationship("Dataset", foreign_keys=[dataset_id])  # type: ignore[name-defined]
    project: Mapped["Project"] = relationship("Project", foreign_keys=[project_id])  # type: ignore[name-defined]
