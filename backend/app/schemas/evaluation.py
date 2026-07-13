from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any
import uuid


class EvaluationRequest(BaseModel):
    problem_type: str = Field(..., pattern="^(classification|regression|clustering)$")
    target_column: Optional[str] = None
    primary_metric: Optional[str] = Field(None, description="Metric used to select the best model. e.g. f1_score, r2")
    cv_folds: int = Field(5, ge=2, le=10)
    algorithms: Optional[list[str]] = Field(None, description="If null, runs a default suite based on problem_type")
    random_state: int = 42


class EvaluationJobResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    project_id: uuid.UUID
    status: str
    problem_type: str
    target_column: Optional[str]
    best_algorithm: Optional[str]
    best_metrics: Optional[dict[str, Any]]
    leaderboard: Optional[list[dict[str, Any]]]
    report: Optional[dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
