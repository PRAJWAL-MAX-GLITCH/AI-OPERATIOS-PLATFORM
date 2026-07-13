"""
Validation API Router
=====================
Endpoints to trigger validation and retrieve results.
All nested under /projects/{project_id}/datasets/{dataset_id}/...
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any
import uuid

from app.schemas.responses import ApiResponse
from app.schemas.validation import ValidationReportResponse, ValidationReportDetail
from app.services.validation_service import validation_service
from app.services.dataset import dataset_service
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user, RequireProjectRole

router = APIRouter()

_READ_ROLES  = ["owner", "admin", "ml_engineer", "data_scientist", "business_analyst", "viewer"]
_WRITE_ROLES = ["owner", "admin", "ml_engineer", "data_scientist"]


@router.post(
    "/projects/{project_id}/datasets/{dataset_id}/validate",
    response_model=ApiResponse[ValidationReportResponse],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def trigger_validation(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
) -> ApiResponse[ValidationReportResponse]:
    """Trigger the full Data Quality validation pipeline on a dataset."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    report = await validation_service.run_validation(db, dataset_id=dataset_id)
    return ApiResponse(data=ValidationReportResponse.model_validate(report))


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/validation",
    response_model=ApiResponse[ValidationReportDetail],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_validation_report(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
) -> ApiResponse[ValidationReportDetail]:
    """Get the latest completed validation report for a dataset."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    report = await validation_service.get_latest_report(db, dataset_id=dataset_id)
    return ApiResponse(data=ValidationReportDetail.model_validate(report))


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/quality-score",
    response_model=ApiResponse[dict[str, Any]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_quality_score(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    """Return just the quality score and grade (lightweight endpoint)."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    report = await validation_service.get_latest_report(db, dataset_id=dataset_id)
    quality = (report.report or {}).get("quality_score", {})
    return ApiResponse(data=quality)


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/statistics",
    response_model=ApiResponse[dict[str, Any]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_statistics(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    """Return numeric and categorical statistics from the latest validation."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    report = await validation_service.get_latest_report(db, dataset_id=dataset_id)
    full   = report.report or {}
    return ApiResponse(data={
        "numeric":     full.get("numeric", {}),
        "categorical": full.get("categorical", {}),
    })


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/outliers",
    response_model=ApiResponse[dict[str, Any]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_outliers(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    """Return outlier statistics from the latest validation."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    report = await validation_service.get_latest_report(db, dataset_id=dataset_id)
    return ApiResponse(data=(report.report or {}).get("outliers", {}))


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/schema",
    response_model=ApiResponse[dict[str, Any]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_schema(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    """Return the inferred schema from the latest validation."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    report = await validation_service.get_latest_report(db, dataset_id=dataset_id)
    return ApiResponse(data=(report.report or {}).get("schema", {}))
