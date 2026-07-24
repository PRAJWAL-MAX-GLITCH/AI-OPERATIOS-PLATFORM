"""
Monitoring Domain Models
========================
Entities for Enterprise Model Monitoring and Drift Detection.
MonitoringBaseline → MonitoringJob → DriftReport
"""
from __future__ import annotations
from sqlalchemy import String, ForeignKey, Integer, Float, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from typing import Optional, Any
from datetime import datetime
from app.models.base import UUIDBaseModel
import uuid


class MonitoringBaseline(UUIDBaseModel):
    """Statistical baseline computed from training/reference data."""
    __tablename__ = "monitoring_baselines"

    model_version_id:   Mapped[uuid.UUID]    = mapped_column(ForeignKey("model_versions.id"), nullable=False, index=True)
    feature_statistics: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    target_distribution: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    metadata_:          Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    computed_at:        Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sample_size:        Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    feature_names:      Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)

    jobs: Mapped[list["MonitoringJob"]] = relationship("MonitoringJob", back_populates="baseline", cascade="all, delete-orphan")


class MonitoringJob(UUIDBaseModel):
    """A scheduled or on-demand monitoring job run."""
    __tablename__ = "monitoring_jobs"

    model_version_id: Mapped[uuid.UUID]      = mapped_column(ForeignKey("model_versions.id"), nullable=False, index=True)
    baseline_id:      Mapped[uuid.UUID]      = mapped_column(ForeignKey("monitoring_baselines.id"), nullable=False, index=True)
    status:           Mapped[str]            = mapped_column(String(50), default="pending")  # pending|running|completed|failed
    window_start:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    window_end:       Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at:       Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message:    Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    celery_task_id:   Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)

    baseline:      Mapped["MonitoringBaseline"] = relationship("MonitoringBaseline", back_populates="jobs")
    drift_reports: Mapped[list["DriftReport"]]  = relationship("DriftReport", back_populates="job", cascade="all, delete-orphan")


class DriftReport(UUIDBaseModel):
    """Results of a drift detection analysis."""
    __tablename__ = "drift_reports"

    job_id:               Mapped[uuid.UUID]     = mapped_column(ForeignKey("monitoring_jobs.id"), nullable=False, index=True)
    drift_detected:       Mapped[bool]          = mapped_column(Boolean, default=False)
    overall_drift_score:  Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    feature_drift_scores: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    psi_scores:           Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    ks_test_results:      Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    recommendations:      Mapped[Optional[list]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    sample_size:          Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
    retrain_triggered:    Mapped[bool]           = mapped_column(Boolean, default=False)

    job: Mapped["MonitoringJob"] = relationship("MonitoringJob", back_populates="drift_reports")
