from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.schemas.responses import ApiResponse
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectMemberCreate, ProjectMemberResponse
from app.services.project import project_service
from app.repositories.project import project_repo
from app.repositories.project_member import project_member_repo
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user, RequireProjectRole

router = APIRouter()

@router.post("", response_model=ApiResponse[ProjectResponse], status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[ProjectResponse]:
    project = await project_service.create_project(db, project_in, current_user)
    return ApiResponse(data=ProjectResponse.model_validate(project))

@router.get("", response_model=ApiResponse[List[ProjectResponse]])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[List[ProjectResponse]]:
    projects = await project_repo.get_user_projects(db, user_id=current_user.id, skip=skip, limit=limit)
    return ApiResponse(data=[ProjectResponse.model_validate(p) for p in projects])

@router.get("/{id}", response_model=ApiResponse[ProjectResponse], dependencies=[Depends(RequireProjectRole(["owner", "admin", "ml_engineer", "data_scientist", "viewer"]))])
async def get_project(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[ProjectResponse]:
    project = await project_service.get_project_or_404(db, id)
    return ApiResponse(data=ProjectResponse.model_validate(project))

@router.post("/{id}/members", response_model=ApiResponse[ProjectMemberResponse], dependencies=[Depends(RequireProjectRole(["owner", "admin"]))])
async def add_project_member(
    id: uuid.UUID,
    member_in: ProjectMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[ProjectMemberResponse]:
    member = await project_service.add_member(db, id, member_in)
    return ApiResponse(data=ProjectMemberResponse.model_validate(member))

@router.get("/{id}/members", response_model=ApiResponse[List[ProjectMemberResponse]], dependencies=[Depends(RequireProjectRole(["owner", "admin", "ml_engineer", "data_scientist", "viewer"]))])
async def list_project_members(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> ApiResponse[List[ProjectMemberResponse]]:
    members = await project_member_repo.get_project_members(db, project_id=id)
    return ApiResponse(data=[ProjectMemberResponse.model_validate(m) for m in members])
