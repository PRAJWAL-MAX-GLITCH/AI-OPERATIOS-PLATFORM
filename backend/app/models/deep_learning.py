"""
Deep Learning Domain Model
==========================
Tracks DL training jobs with epoch-level metrics, checkpoints, and configuration.
"""
from sqlalchemy import String, ForeignKey, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Any
from app.models.base import UUIDBaseModel
import uuid


class DLTrainingJob(UUIDBaseModel):
    __tablename__ = "dl_training_jobs"

    project_id:       Mapped[uuid.UUID]  = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    dataset_id:       Mapped[uuid.UUID]  = mapped_column(ForeignKey("datasets.id"), nullable=False, index=True)
    
    # Job state
    status:           Mapped[str]         = mapped_column(String(50),   default="pending")   # pending|running|completed|failed
    error_message:    Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    # Architecture config
    problem_type:     Mapped[str]         = mapped_column(String(50),  nullable=False)  # binary_classification|multiclass_classification|regression
    target_column:    Mapped[str]         = mapped_column(String(255), nullable=False)
    architecture:     Mapped[str]         = mapped_column(String(100), default="fully_connected")

    # Training hyperparameters (JSONB)
    hyperparameters:  Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Progress tracking
    current_epoch:    Mapped[int]         = mapped_column(Integer, default=0)
    total_epochs:     Mapped[int]         = mapped_column(Integer, default=50)
    best_val_loss:    Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    best_epoch:       Mapped[Optional[int]]   = mapped_column(Integer, nullable=True)

    # Output paths
    checkpoint_dir:   Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    best_model_path:  Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    tensorboard_dir:  Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Epoch-by-epoch metrics history
    metrics_history:  Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    final_metrics:    Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # MLflow tracking
    mlflow_run_id:    Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    project: Mapped["Project"] = relationship("Project", foreign_keys=[project_id])  # type: ignore
    dataset: Mapped["Dataset"] = relationship("Dataset", foreign_keys=[dataset_id])  # type: ignore
