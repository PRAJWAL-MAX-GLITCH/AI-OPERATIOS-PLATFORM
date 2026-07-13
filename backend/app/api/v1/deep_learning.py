"""
Deep Learning API Router
=========================
Endpoints for DL training, job management, and inference.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
import uuid

from app.schemas.responses import ApiResponse
from app.schemas.deep_learning import DLTrainRequest, DLPredictRequest, DLJobResponse
from app.services.dl_service import dl_service
from app.services.deep_learning.config import get_device_info
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user, RequireProjectRole

router = APIRouter()

_READ_ROLES  = ["owner", "admin", "ml_engineer", "data_scientist", "viewer"]
_WRITE_ROLES = ["owner", "admin", "ml_engineer", "data_scientist"]


@router.get(
    "/projects/{project_id}/deep-learning/devices",
    response_model=ApiResponse[dict],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_device_info_endpoint(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """Returns available compute devices (GPU/CPU detection)."""
    return ApiResponse(data=get_device_info())


@router.post(
    "/projects/{project_id}/deep-learning/train",
    response_model=ApiResponse[DLJobResponse],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def start_dl_training(
    project_id: uuid.UUID,
    request: DLTrainRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[DLJobResponse]:
    """
    Start a deep learning training job.
    Supports binary_classification, multiclass_classification, regression.
    """
    try:
        job = await dl_service.start_training(
            db=db,
            project_id=project_id,
            dataset_id=request.dataset_id,
            request=request.model_dump(),
        )
        return ApiResponse(data=DLJobResponse.model_validate(job))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/projects/{project_id}/deep-learning/jobs",
    response_model=ApiResponse[List[DLJobResponse]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def list_dl_jobs(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[DLJobResponse]]:
    """List all deep learning training jobs for a project."""
    jobs = await dl_service.list_jobs(db, project_id)
    return ApiResponse(data=[DLJobResponse.model_validate(j) for j in jobs])


@router.get(
    "/projects/{project_id}/deep-learning/jobs/{job_id}",
    response_model=ApiResponse[DLJobResponse],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_dl_job(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[DLJobResponse]:
    """Get status, metrics, and config for a specific DL job."""
    job = await dl_service.get_job(db, job_id)
    return ApiResponse(data=DLJobResponse.model_validate(job))


@router.post(
    "/projects/{project_id}/deep-learning/jobs/{job_id}/predict",
    response_model=ApiResponse[dict],
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def dl_predict(
    project_id: uuid.UUID,
    job_id: uuid.UUID,
    request: DLPredictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict]:
    """
    Run inference using a trained DL model.
    Pass features as a flat dict of column_name: value.
    """
    try:
        result = await dl_service.predict(db, job_id, request.features)
        return ApiResponse(data=result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
