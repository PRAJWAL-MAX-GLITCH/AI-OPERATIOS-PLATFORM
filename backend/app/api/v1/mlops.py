"""
MLOps API Router
================
Endpoints for Model Registry and Experiment tracking via MLflow wrapper.
"""
from fastapi import APIRouter, Depends, status, HTTPException
from typing import Any, List
import uuid

from app.schemas.responses import ApiResponse
from app.services.mlops.model_registry import model_registry
from app.models.domain import User
from app.api.dependencies import get_current_user, RequireProjectRole
from pydantic import BaseModel

router = APIRouter()

_READ_ROLES  = ["owner", "admin", "ml_engineer", "data_scientist", "business_analyst", "viewer"]
_WRITE_ROLES = ["owner", "admin", "ml_engineer", "data_scientist"]


class StageTransitionRequest(BaseModel):
    version: str
    stage: str
    archive_existing: bool = True


@router.get(
    "/models",
    response_model=ApiResponse[List[dict[str, Any]]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def list_registered_models(
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[dict[str, Any]]]:
    """List all registered models across the registry."""
    try:
        models = model_registry.get_registered_models()
        return ApiResponse(data=models)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/models/{model_name}/versions",
    response_model=ApiResponse[List[dict[str, Any]]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_model_versions(
    model_name: str,
    stages: List[str] = None,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[dict[str, Any]]]:
    """Get all versions of a specific registered model."""
    try:
        versions = model_registry.get_latest_versions(model_name, stages)
        return ApiResponse(data=versions)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/models/{model_name}/stage",
    response_model=ApiResponse[str],
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def transition_model_stage(
    model_name: str,
    request: StageTransitionRequest,
    current_user: User = Depends(get_current_user),
) -> ApiResponse[str]:
    """
    Transition a model version to a specific stage.
    Stages: None, Staging, Production, Archived.
    """
    try:
        model_registry.transition_stage(
            model_name=model_name,
            version=request.version,
            stage=request.stage,
            archive_existing=request.archive_existing
        )
        return ApiResponse(data=f"Successfully transitioned {model_name} v{request.version} to {request.stage}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
