from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Any
import uuid


class DatasetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    dataset_type: str = Field("raw", pattern="^(raw|processed|training|validation|production)$")


class DatasetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    dataset_type: Optional[str] = Field(None, pattern="^(raw|processed|training|validation|production)$")


class DatasetResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    original_filename: str
    file_format: str
    file_size_bytes: int
    dataset_type: str
    status: str
    row_count: Optional[int]
    column_count: Optional[int]
    checksum: str
    version: int
    project_id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DatasetPreview(BaseModel):
    columns: list[str]
    rows: list[dict[str, Any]]
    total_rows: int
    page: int
    page_size: int


class DatasetVersionResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    version: int
    original_filename: str
    checksum: str
    file_size_bytes: int
    row_count: Optional[int]
    column_count: Optional[int]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
