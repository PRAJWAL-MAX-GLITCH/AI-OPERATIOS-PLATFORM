from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from typing import Optional, Any
from app.models.base import UUIDBaseModel
import uuid


class EvaluationJob(UUIDBaseModel):
    __tablename__ = "evaluation_jobs"

    dataset_id:    Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), nullable=False, index=True)
    project_id:    Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    status:        Mapped[str]       = mapped_column(String(50), default="pending")  # pending|running|completed|failed
    problem_type:  Mapped[str]       = mapped_column(String(50), nullable=False)     # classification|regression|clustering
    target_column: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Leaderboard of all evaluated algorithms
    leaderboard:   Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    
    # Best model reference and details
    best_algorithm: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    best_metrics:   Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    best_model_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    # Explanation / Report
    report:         Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    error_message:  Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    
    # Store the preprocessing pipeline path to recreate features
    preprocessing_pipeline_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    dataset: Mapped["Dataset"] = relationship("Dataset", foreign_keys=[dataset_id])  # type: ignore[name-defined]
    project: Mapped["Project"] = relationship("Project", foreign_keys=[project_id])  # type: ignore[name-defined]
