"""
Workflow Domain Models
======================
Entities for the Enterprise AI Workflow Orchestration system.
WorkflowDefinition → WorkflowRun → TaskRun
Additional: WorkflowEvent for event-driven triggers.
"""
from __future__ import annotations
from sqlalchemy import String, ForeignKey, Integer, Float, Text, Boolean, DateTime, JSON as SAJSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import Optional, Any, List
from datetime import datetime
from app.models.base import UUIDBaseModel
import uuid


class WorkflowDefinition(UUIDBaseModel):
    """A reusable workflow DAG definition."""
    __tablename__ = "workflow_definitions"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dag_definition: Mapped[Optional[dict[str, Any]]] = mapped_column(SAJSON().with_variant(JSONB, 'postgresql'), nullable=True)
    default_parameters: Mapped[Optional[dict[str, Any]]] = mapped_column(SAJSON().with_variant(JSONB, 'postgresql'), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)

    runs: Mapped[List["WorkflowRun"]] = relationship("WorkflowRun", back_populates="definition", cascade="all, delete-orphan")


class WorkflowRun(UUIDBaseModel):
    """A single execution of a workflow definition."""
    __tablename__ = "workflow_runs"

    definition_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_definitions.id"), nullable=False, index=True)
    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending|running|completed|failed|cancelled
    parameters: Mapped[Optional[dict[str, Any]]] = mapped_column(SAJSON().with_variant(JSONB, 'postgresql'), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    run_output: Mapped[Optional[dict[str, Any]]] = mapped_column(SAJSON().with_variant(JSONB, 'postgresql'), nullable=True)
    celery_task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    definition: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="runs")
    task_runs: Mapped[List["TaskRun"]] = relationship("TaskRun", back_populates="workflow_run", cascade="all, delete-orphan")


class TaskRun(UUIDBaseModel):
    """A single step/task within a workflow run."""
    __tablename__ = "task_runs"

    workflow_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workflow_runs.id"), nullable=False, index=True)
    # Compatibility fields – original code expects `task_id` and `task_name`
    task_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    task_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    input_data: Mapped[Optional[dict[str, Any]]] = mapped_column(SAJSON().with_variant(JSONB, 'postgresql'), nullable=True)
    output_data: Mapped[Optional[dict[str, Any]]] = mapped_column(SAJSON().with_variant(JSONB, 'postgresql'), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    step_index: Mapped[int] = mapped_column(Integer, default=0)

    workflow_run: Mapped["WorkflowRun"] = relationship("WorkflowRun", back_populates="task_runs")


class WorkflowEvent(UUIDBaseModel):
    """Event records used by the EventBus to trigger workflows."""
    __tablename__ = "workflow_events"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[Optional[dict[str, Any]]] = mapped_column(SAJSON().with_variant(JSONB, 'postgresql'), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="pending")  # pending|processed|failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
