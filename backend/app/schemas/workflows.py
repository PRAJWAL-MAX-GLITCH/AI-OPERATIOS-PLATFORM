"""
Workflow API Schemas
====================
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
import uuid
from datetime import datetime

class TaskDefinitionSchema(BaseModel):
    id: str
    type: str

class EdgeDefinitionSchema(BaseModel):
    from_: str = Field(alias="from")
    to: str

class WorkflowDAGSchema(BaseModel):
    tasks: List[TaskDefinitionSchema]
    edges: List[EdgeDefinitionSchema]

class WorkflowDefinitionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dag_definition: WorkflowDAGSchema
    default_parameters: Optional[Dict[str, Any]] = {}

class WorkflowDefinitionResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    dag_definition: Dict[str, Any]
    default_parameters: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class WorkflowRunCreate(BaseModel):
    parameters: Optional[Dict[str, Any]] = {}
    project_id: Optional[uuid.UUID] = None

class TaskRunResponse(BaseModel):
    id: uuid.UUID
    task_id: str
    task_type: str
    status: str
    retries: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True

class WorkflowRunResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    tasks: List[TaskRunResponse] = []

    class Config:
        from_attributes = True
