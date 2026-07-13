from sqlalchemy import String, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Any
from app.models.base import UUIDBaseModel
import uuid


class PredictionLog(UUIDBaseModel):
    __tablename__ = "prediction_logs"

    project_id:    Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False, index=True)
    model_name:    Mapped[str]       = mapped_column(String(255), nullable=False, index=True)
    model_version: Mapped[str]       = mapped_column(String(50), nullable=False)
    
    latency_ms:    Mapped[float]     = mapped_column(Float, nullable=False)
    confidence:    Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Store complete payload in JSONB
    input_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    prediction_result: Mapped[Any] = mapped_column(JSONB, nullable=False)
    
    # If explanations are generated, store the results or metadata
    explanation:   Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    project: Mapped["Project"] = relationship("Project", foreign_keys=[project_id])  # type: ignore[name-defined]
