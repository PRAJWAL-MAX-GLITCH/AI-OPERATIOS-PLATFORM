"""
Agent API Schemas
=================
"""
from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
import uuid
from datetime import datetime


class AgentRunRequest(BaseModel):
    agent_type: str = Field(..., description="The type of agent to run (e.g., 'planner')")
    task_title: str = Field(..., description="The main objective for the agent")
    task_description: Optional[str] = None
    project_id: Optional[uuid.UUID] = None


class AgentTaskResponse(BaseModel):
    task_id: uuid.UUID
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime


class AgentRunStatusResponse(BaseModel):
    run_id: uuid.UUID
    agent_type: str
    status: str
    total_steps: int
    started_at: datetime
    completed_at: Optional[datetime] = None


class AgentHistoryResponse(BaseModel):
    messages: List[Dict[str, Any]]
