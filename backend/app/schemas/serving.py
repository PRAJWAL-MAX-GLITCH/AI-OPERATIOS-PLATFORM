from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any, List
import uuid


class PredictRequest(BaseModel):
    features: dict[str, Any]
    explain: bool = False
    version: Optional[str] = None  # If none, uses latest production model


class PredictBatchRequest(BaseModel):
    dataset_id: uuid.UUID
    explain: bool = False
    version: Optional[str] = None


class PredictResponse(BaseModel):
    prediction: Any
    confidence: Optional[float] = None
    explanation: Optional[dict[str, Any]] = None
    latency_ms: float
    model_version: str


class PredictionLogResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    model_name: str
    model_version: str
    latency_ms: float
    confidence: Optional[float]
    input_payload: dict[str, Any]
    prediction_result: Any
    explanation: Optional[dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
