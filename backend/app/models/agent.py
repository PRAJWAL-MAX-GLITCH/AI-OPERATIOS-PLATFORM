"""
Agent Domain Models
===================
Entities for the Enterprise AI Agent Platform.
AgentTask → AgentRun → AgentMessage
"""
from __future__ import annotations
from sqlalchemy import String, ForeignKey, Integer, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from typing import Optional, Any
from app.models.base import UUIDBaseModel
import uuid


class AgentTask(UUIDBaseModel):
    """A task definition submitted by a user to an agent."""
    __tablename__ = "agent_tasks"

    user_id:       Mapped[uuid.UUID]       = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    project_id:    Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.id"), nullable=True, index=True)
    agent_type:    Mapped[str]             = mapped_column(String(100), nullable=False)
    title:         Mapped[Optional[str]]   = mapped_column(String(255), nullable=True)
    description:   Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    status:        Mapped[str]             = mapped_column(String(50), default="pending")  # pending|running|completed|failed|cancelled
    input_data:    Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    result:        Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    error_message: Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    priority:      Mapped[int]             = mapped_column(Integer, default=0)
    celery_task_id: Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)

    runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="task", cascade="all, delete-orphan")



class AgentRun(UUIDBaseModel):
    """A single execution run of an agent task."""
    __tablename__ = "agent_runs"

    task_id:       Mapped[uuid.UUID]       = mapped_column(ForeignKey("agent_tasks.id"), nullable=False, index=True)
    agent_type:    Mapped[str]             = mapped_column(String(100), nullable=False)
    status:        Mapped[str]             = mapped_column(String(50), default="running")  # running|completed|failed
    started_at:    Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    completed_at:  Mapped[Optional[str]]   = mapped_column(String(50), nullable=True)
    duration_ms:   Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    steps_taken:   Mapped[int]             = mapped_column(Integer, default=0)
    tools_used:    Mapped[Optional[list]]  = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    final_output:  Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    run_metadata:  Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)

    task:     Mapped["AgentTask"]       = relationship("AgentTask", back_populates="runs")
    messages: Mapped[list["AgentMessage"]] = relationship("AgentMessage", back_populates="run", cascade="all, delete-orphan")


class AgentMessage(UUIDBaseModel):
    """Individual step/message in an agent run (thought, action, observation)."""
    __tablename__ = "agent_messages"

    run_id:       Mapped[uuid.UUID]       = mapped_column(ForeignKey("agent_runs.id"), nullable=False, index=True)
    role:         Mapped[str]             = mapped_column(String(30), nullable=False)  # thought|action|observation|final
    content:      Mapped[str]             = mapped_column(Text, nullable=False)
    tool_name:    Mapped[Optional[str]]   = mapped_column(String(100), nullable=True)
    tool_input:   Mapped[Optional[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    tool_output:  Mapped[Optional[str]]   = mapped_column(Text, nullable=True)
    step_index:   Mapped[int]             = mapped_column(Integer, default=0)

    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="messages")
