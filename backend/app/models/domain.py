from sqlalchemy import String, ForeignKey, Boolean, DateTime, BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from typing import List, Optional, Any
from datetime import datetime
from app.models.base import UUIDBaseModel
import uuid


class User(UUIDBaseModel):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    projects: Mapped[List["Project"]] = relationship(back_populates="owner")
    project_memberships: Mapped[List["ProjectMember"]] = relationship(back_populates="user")
    datasets: Mapped[List["Dataset"]] = relationship(back_populates="created_by")


class Project(UUIDBaseModel):
    __tablename__ = "projects"
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    visibility: Mapped[str] = mapped_column(String(50), default="private", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    tags: Mapped[Optional[list[Any]]] = mapped_column(JSONB, nullable=True)

    owner: Mapped["User"] = relationship(back_populates="projects")
    members: Mapped[List["ProjectMember"]] = relationship(back_populates="project")
    datasets: Mapped[List["Dataset"]] = relationship(back_populates="project")
    experiments: Mapped[List["Experiment"]] = relationship(back_populates="project")
    documents: Mapped[List["Document"]] = relationship(back_populates="project")
    chat_sessions: Mapped[List["ChatSession"]] = relationship(back_populates="project")


class ProjectMember(UUIDBaseModel):
    __tablename__ = "project_members"
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)

    project: Mapped["Project"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="project_memberships")


class Dataset(UUIDBaseModel):
    __tablename__ = "datasets"
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    dataset_type: Mapped[str] = mapped_column(String(50), nullable=False)  # raw, processed, training, validation
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)   # csv, xlsx, json, parquet
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)      # SHA-256 hex
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="processing", nullable=False)  # processing, ready, error
    profile: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    schema_info: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="datasets")
    created_by: Mapped["User"] = relationship(back_populates="datasets")
    versions: Mapped[List["DatasetVersion"]] = relationship(back_populates="dataset")


class DatasetVersion(UUIDBaseModel):
    __tablename__ = "dataset_versions"
    dataset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="versions")


class Document(UUIDBaseModel):
    __tablename__ = "documents"
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="documents")


class Experiment(UUIDBaseModel):
    __tablename__ = "experiments"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mlflow_experiment_id: Mapped[Optional[str]] = mapped_column(String(255))
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="experiments")
    model_versions: Mapped[List["ModelVersion"]] = relationship(back_populates="experiment")


class ModelVersion(UUIDBaseModel):
    __tablename__ = "model_versions"
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    s3_model_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    metrics: Mapped[Optional[str]] = mapped_column(String)
    experiment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("experiments.id"), nullable=False)

    experiment: Mapped["Experiment"] = relationship(back_populates="model_versions")
    predictions: Mapped[List["Prediction"]] = relationship(back_populates="model_version")


class Prediction(UUIDBaseModel):
    __tablename__ = "predictions"
    input_data: Mapped[str] = mapped_column(String, nullable=False)
    output_data: Mapped[str] = mapped_column(String, nullable=False)
    model_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("model_versions.id"), nullable=False)

    model_version: Mapped["ModelVersion"] = relationship(back_populates="predictions")


class ChatSession(UUIDBaseModel):
    __tablename__ = "chat_sessions"
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Chat")
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id"), nullable=False)

    project: Mapped["Project"] = relationship(back_populates="chat_sessions")
