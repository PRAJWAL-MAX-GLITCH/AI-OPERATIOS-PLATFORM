from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any
import uuid

from app.schemas.responses import ApiResponse
from app.schemas.dataset import DatasetResponse, DatasetPreview, DatasetVersionResponse
from app.services.dataset import dataset_service
from app.repositories.dataset import dataset_repo
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user, RequireProjectRole

router = APIRouter()

_WRITE_ROLES = ["owner", "admin", "ml_engineer", "data_scientist"]
_READ_ROLES  = ["owner", "admin", "ml_engineer", "data_scientist", "business_analyst", "viewer"]


@router.post(
    "/projects/{project_id}/datasets/upload",
    response_model=ApiResponse[DatasetResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def upload_dataset(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str | None = Form(None),
    dataset_type: str = Form("raw"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[DatasetResponse]:
    """Upload a new dataset file and trigger profiling."""
    dataset = await dataset_service.upload_dataset(
        db,
        project_id=project_id,
        file=file,
        name=name,
        description=description,
        dataset_type=dataset_type,
        current_user=current_user,
    )
    return ApiResponse(data=DatasetResponse.model_validate(dataset))


@router.get(
    "/projects/{project_id}/datasets",
    response_model=ApiResponse[List[DatasetResponse]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def list_datasets(
    project_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[DatasetResponse]]:
    """List all datasets in a project."""
    datasets = await dataset_repo.get_by_project(db, project_id=project_id, skip=skip, limit=limit)
    return ApiResponse(data=[DatasetResponse.model_validate(d) for d in datasets])


@router.get(
    "/projects/{project_id}/datasets/{id}",
    response_model=ApiResponse[DatasetResponse],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_dataset(
    project_id: uuid.UUID,
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[DatasetResponse]:
    """Get a single dataset by ID."""
    dataset = await dataset_service.get_dataset_or_404(db, id)
    dataset_service.assert_project_ownership(dataset, project_id)
    return ApiResponse(data=DatasetResponse.model_validate(dataset))


@router.get(
    "/projects/{project_id}/datasets/{id}/profile",
    response_model=ApiResponse[dict[str, Any]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_dataset_profile(
    project_id: uuid.UUID,
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict[str, Any]]:
    """Return the stored data profile (rows, cols, missing values, statistics)."""
    dataset = await dataset_service.get_dataset_or_404(db, id)
    dataset_service.assert_project_ownership(dataset, project_id)
    profile = dataset.profile or {}
    return ApiResponse(data=profile)


@router.get(
    "/projects/{project_id}/datasets/{id}/preview",
    response_model=ApiResponse[DatasetPreview],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def preview_dataset(
    project_id: uuid.UUID,
    id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[DatasetPreview]:
    """Preview up to page_size rows of the dataset."""
    dataset = await dataset_service.get_dataset_or_404(db, id)
    dataset_service.assert_project_ownership(dataset, project_id)
    preview = await dataset_service.get_preview(dataset, page=page, page_size=page_size)
    return ApiResponse(data=DatasetPreview(**preview))


@router.get(
    "/projects/{project_id}/datasets/{id}/versions",
    response_model=ApiResponse[List[DatasetVersionResponse]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def list_dataset_versions(
    project_id: uuid.UUID,
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[DatasetVersionResponse]]:
    """List all historical versions of a dataset."""
    dataset = await dataset_service.get_dataset_or_404(db, id)
    dataset_service.assert_project_ownership(dataset, project_id)
    versions = await dataset_repo.get_versions(db, dataset_id=id)
    return ApiResponse(data=[DatasetVersionResponse.model_validate(v) for v in versions])


@router.post(
    "/projects/{project_id}/datasets/{id}/rollback",
    response_model=ApiResponse[DatasetResponse],
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def rollback_dataset(
    project_id: uuid.UUID,
    id: uuid.UUID,
    target_version: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[DatasetResponse]:
    """Roll back a dataset to a specific historical version."""
    dataset = await dataset_service.get_dataset_or_404(db, id)
    dataset_service.assert_project_ownership(dataset, project_id)
    rolled = await dataset_service.rollback(db, dataset, target_version)
    return ApiResponse(data=DatasetResponse.model_validate(rolled))


@router.delete(
    "/projects/{project_id}/datasets/{id}",
    response_model=ApiResponse[dict[str, str]],
    dependencies=[Depends(RequireProjectRole(["owner", "admin"]))],
)
async def delete_dataset(
    project_id: uuid.UUID,
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[dict[str, str]]:
    """Soft-delete a dataset."""
    dataset = await dataset_service.get_dataset_or_404(db, id)
    dataset_service.assert_project_ownership(dataset, project_id)
    await dataset_repo.remove(db, id=id)
    return ApiResponse(data={"message": "Dataset deleted successfully"})
