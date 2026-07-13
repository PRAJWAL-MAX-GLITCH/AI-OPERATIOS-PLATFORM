from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
import uuid
from typing import Optional, List, Any

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    visibility: str = Field("private", pattern="^(private|public)$")
    tags: Optional[List[str]] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=1024)
    visibility: Optional[str] = Field(None, pattern="^(private|public)$")
    tags: Optional[List[str]] = None
    status: Optional[str] = Field(None, pattern="^(active|archived)$")

class ProjectResponse(ProjectBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectMemberBase(BaseModel):
    role: str = Field("viewer", pattern="^(owner|admin|ml_engineer|data_scientist|business_analyst|viewer)$")

class ProjectMemberCreate(ProjectMemberBase):
    user_id: uuid.UUID

class ProjectMemberUpdate(ProjectMemberBase):
    pass

class ProjectMemberResponse(ProjectMemberBase):
    id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
