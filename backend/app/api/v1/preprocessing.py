"""
Preprocessing API Router
========================
All endpoints nested under /projects/{project_id}/datasets/{dataset_id}/...
Enforces RBAC and the validation gate (dataset must be validated first).
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
import uuid

from app.schemas.responses import ApiResponse
from app.schemas.preprocessing import (
    PreprocessingRequest, PreprocessingReportResponse, PreprocessingReportDetail
)
from app.services.preprocessing_service import preprocessing_service
from app.services.preprocessing.serializer import list_pipelines
from app.services.dataset import dataset_service
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user, RequireProjectRole

router = APIRouter()

_READ_ROLES  = ["owner", "admin", "ml_engineer", "data_scientist", "business_analyst", "viewer"]
_WRITE_ROLES = ["owner", "admin", "ml_engineer", "data_scientist"]


@router.post(
    "/projects/{project_id}/datasets/{dataset_id}/preprocess",
    response_model=ApiResponse[PreprocessingReportResponse],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def trigger_preprocessing(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    request:     PreprocessingRequest,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[PreprocessingReportResponse]:
    """
    Run the full Feature Engineering & Preprocessing pipeline.
    Dataset MUST be validated first (POST .../validate).
    """
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    report = await preprocessing_service.run_preprocessing(db, dataset_id, request)
    return ApiResponse(data=PreprocessingReportResponse.model_validate(report))


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/pipeline",
    response_model=ApiResponse[PreprocessingReportDetail],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_pipeline(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[PreprocessingReportDetail]:
    """Get the latest completed preprocessing pipeline report."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    report = await preprocessing_service.get_latest_report(db, dataset_id)
    return ApiResponse(data=PreprocessingReportDetail.model_validate(report))


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/features",
    response_model=ApiResponse[dict[str, Any]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_features(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    """Get the output feature list and shape from the latest pipeline."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    report = await preprocessing_service.get_latest_report(db, dataset_id)
    return ApiResponse(data={
        "output_columns": report.output_columns,
        "output_shape":   report.output_shape,
        "input_shape":    report.input_shape,
    })


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/pipeline/history",
    response_model=ApiResponse[List[PreprocessingReportResponse]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_pipeline_history(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[List[PreprocessingReportResponse]]:
    """List all historical preprocessing runs for a dataset."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    reports = await preprocessing_service.get_pipeline_history(db, dataset_id)
    return ApiResponse(data=[PreprocessingReportResponse.model_validate(r) for r in reports])
