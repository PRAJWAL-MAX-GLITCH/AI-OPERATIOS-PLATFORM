"""
Monitoring API Schemas
======================
"""
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
import uuid
from datetime import datetime

class MonitoringJobCreate(BaseModel):
    model_version_id: uuid.UUID
    baseline_id: uuid.UUID
    window_start: datetime
    window_end: datetime

class MonitoringJobResponse(BaseModel):
    id: uuid.UUID
    model_version_id: uuid.UUID
    baseline_id: uuid.UUID
    status: str
    window_start: datetime
    window_end: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]

    class Config:
        from_attributes = True

class DriftReportResponse(BaseModel):
    id: uuid.UUID
    job_id: uuid.UUID
    overall_drift_score: float
    has_data_drift: str
    has_prediction_drift: str
    feature_drift_details: Dict[str, Any]
    performance_metrics: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True

class RetrainTriggerCreate(BaseModel):
    model_version_id: uuid.UUID
    reason: str
