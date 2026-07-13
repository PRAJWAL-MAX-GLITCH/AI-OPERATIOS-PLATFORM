from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Optional, Any
import uuid


class PreprocessingRequest(BaseModel):
    mode: str = Field("auto", pattern="^(auto|manual)$")
    target_column: Optional[str] = None
    drop_columns: list[str] = []
    missing_strategy: str = "auto"
    encoding_strategy: str = "auto"
    scaling_strategy: str = "auto"
    auto_transform_skewed: bool = True
    polynomial_degree: int = Field(0, ge=0, le=3)
    selection_strategy: str = "auto"


class PreprocessingReportResponse(BaseModel):
    id: uuid.UUID
    dataset_id: uuid.UUID
    status: str
    input_shape: Optional[list[int]]
    output_shape: Optional[list[int]]
    output_columns: Optional[list[str]]
    pipeline_path: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreprocessingReportDetail(PreprocessingReportResponse):
    report: Optional[dict[str, Any]]

    model_config = ConfigDict(from_attributes=True)
