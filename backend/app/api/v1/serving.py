"""
Serving API Router
==================
Endpoints for Online Inference and Batch Predictions.
"""
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, List
import uuid

from app.schemas.responses import ApiResponse
from app.schemas.serving import PredictRequest, PredictionLogResponse
from app.services.serving_service import serving_service
from app.models.domain import User
from app.api.dependencies import get_db, get_current_user, RequireProjectRole

router = APIRouter()

_READ_ROLES  = ["owner", "admin", "ml_engineer", "data_scientist", "business_analyst", "viewer"]
_WRITE_ROLES = ["owner", "admin", "ml_engineer", "data_scientist", "application"]


@router.post(
    "/projects/{project_id}/models/{model_name}/predict",
    response_model=ApiResponse[PredictionLogResponse],
    dependencies=[Depends(RequireProjectRole(_WRITE_ROLES))],
)
async def predict_online(
    project_id: uuid.UUID,
    model_name: str,
    request: PredictRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[PredictionLogResponse]:
    """
    Run a single online prediction.
    Features should be passed as a dictionary of column_name: value.
    Optionally request SHAP/LIME explanation.
    """
    try:
        log_entry = await serving_service.predict_online(db, project_id, model_name, request)
        return ApiResponse(data=PredictionLogResponse.model_validate(log_entry))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/projects/{project_id}/models/{model_name}/predictions",
    response_model=ApiResponse[List[PredictionLogResponse]],
    dependencies=[Depends(RequireProjectRole(_READ_ROLES))],
)
async def get_prediction_history(
    project_id: uuid.UUID,
    model_name: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse[List[PredictionLogResponse]]:
    """Get the history of predictions made by a specific model."""
    history = await serving_service.get_prediction_history(db, project_id, model_name, limit)
    return ApiResponse(data=[PredictionLogResponse.model_validate(h) for h in history])
