from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Any
import uuid


class ValidationReportResponse(BaseModel):
    id:            uuid.UUID
    dataset_id:    uuid.UUID
    status:        str
    quality_score: Optional[float]
    grade:         Optional[str]
    error_message: Optional[str]
    created_at:    datetime
    updated_at:    datetime

    model_config = ConfigDict(from_attributes=True)


class ValidationReportDetail(ValidationReportResponse):
    report: Optional[dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)
