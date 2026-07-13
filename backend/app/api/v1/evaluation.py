"""
Evaluation API Router
=====================
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
import uuid

from app.schemas.responses import ApiResponse
from app.schemas.evaluation import EvaluationRequest, EvaluationJobResponse
from app.services.evaluation_service import evaluation_service
from app.services.dataset import dataset_service
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user, RequireProjectRole

router = APIRouter()

_READ_ROLES  = ["owner", "admin", "ml_engineer", "data_scientist", "business_analyst", "viewer"]
_WRITE_ROLES = ["owner", "admin", "ml_engineer", "data_scientist"]


@router.post(
    "/projects/{project_id}/datasets/{dataset_id}/evaluation/start",
    response_model=ApiResponse[EvaluationJobResponse],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def start_evaluation(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    request:     EvaluationRequest,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[EvaluationJobResponse]:
    """Start AutoML Evaluation Job."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    job = await evaluation_service.start_evaluation(db, project_id, dataset_id, request)
    return ApiResponse(data=EvaluationJobResponse.model_validate(job))


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/evaluation/jobs",
    response_model=ApiResponse[List[EvaluationJobResponse]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_evaluation_jobs(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[List[EvaluationJobResponse]]:
    """List evaluation jobs for a dataset."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    jobs = await evaluation_service.get_jobs_for_dataset(db, dataset_id)
    return ApiResponse(data=[EvaluationJobResponse.model_validate(j) for j in jobs])


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/evaluation/jobs/{job_id}",
    response_model=ApiResponse[EvaluationJobResponse],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_evaluation_job(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    job_id:      uuid.UUID,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[EvaluationJobResponse]:
    """Get evaluation job by id."""
    dataset = await dataset_service.get_dataset_or_404(db, dataset_id)
    dataset_service.assert_project_ownership(dataset, project_id)
    job = await evaluation_service.get_job(db, job_id)
    if job.dataset_id != dataset_id or job.project_id != project_id:
        raise ValueError("Job does not belong to this dataset/project.")
    return ApiResponse(data=EvaluationJobResponse.model_validate(job))


@router.get(
    "/projects/{project_id}/datasets/{dataset_id}/models/leaderboard",
    response_model=ApiResponse[list[dict[str, Any]]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_leaderboard(
    project_id:  uuid.UUID,
    dataset_id:  uuid.UUID,
    db:          AsyncSession = Depends(get_db),
    current_user: User        = Depends(get_current_user),
) -> ApiResponse[list[dict[str, Any]]]:
    """Get the latest leaderboard for a dataset."""
    jobs = await evaluation_service.get_jobs_for_dataset(db, dataset_id)
    completed = [j for j in jobs if j.status == "completed" and j.leaderboard]
    if not completed:
        return ApiResponse(data=[])
    
    return ApiResponse(data=completed[0].leaderboard)
