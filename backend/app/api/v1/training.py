"""
Training API Router
===================
Endpoints nested under /projects/{project_id}/datasets/{dataset_id}/...
Enforces RBAC and requires preprocessing to be done.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
import uuid

from app.schemas.responses import ApiResponse
from app.schemas.training import TrainingRequest, TrainingJobResponse
from app.services.training_service import training_service
from app.services.dataset import dataset_service
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user, RequireProjectRole

router = APIRouter()

_READ_ROLES  = ["owner", "admin", "ml_engineer", "data_scientist", "business_analyst", "viewer"]
_WRITE_ROLES = ["owner", "admin", "ml_engineer", "data_scientist"]


@router.post(
    "/projects/{project_id}/datasets/{dataset_id}/training/start",
    response_model=ApiResponse[TrainingJobResponse],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def start_training(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    request:     TrainingRequest,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[TrainingJobResponse]:
    """
    Start an ML training job.
    Dataset MUST be preprocessed first (POST .../preprocess).
    """
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    job = await training_service.start_training(db, project_id, dataset_id, request)
    return ApiResponse(data=TrainingJobResponse.model_validate(job))


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/training/jobs",
    response_model=ApiResponse[List[TrainingJobResponse]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_training_jobs(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[List[TrainingJobResponse]]:
    """List all training jobs for a dataset."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    jobs = await training_service.get_jobs_for_dataset(db, dataset_id)
    return ApiResponse(data=[TrainingJobResponse.model_validate(j) for j in jobs])


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/training/jobs/{job_id}",
    response_model=ApiResponse[TrainingJobResponse],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_training_job(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    job_id:      uuid.UUID,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[TrainingJobResponse]:
    """Get details of a specific training job."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    job = await training_service.get_job(db, job_id)
    if job.dataset_id != dataset_id or job.project_id != project_id:
        raise ValueError("Job does not belong to this dataset/project.")
    return ApiResponse(data=TrainingJobResponse.model_validate(job))
