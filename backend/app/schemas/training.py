from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any
import uuid


class TrainingRequest(BaseModel):
    problem_type: str = Field(..., pattern="^(classification|regression|clustering)$")
    target_column: Optional[str] = None
    algorithm: str = Field(..., description="e.g., random_forest, logistic_regression, xgboost")
    test_size: float = Field(0.2, ge=0.01, le=0.99)
    random_state: int = 42
    parameters: dict[str, Any] = Field(default_factory=dict, description="Hyperparameters for the algorithm")


class TrainingJobResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    project_id: uuid.UUID
    status: str
    algorithm: str
    problem_type: str
    target_column: Optional[str]
    metrics: Optional[dict[str, Any]]
    model_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
