"""
Monitoring API Router
=====================
Endpoints for Enterprise Model Monitoring and Drift Detection.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.models.domain import User
from app.models.monitoring import MonitoringJob, DriftReport, MonitoringBaseline
from app.schemas.monitoring import MonitoringJobCreate, MonitoringJobResponse, DriftReportResponse, RetrainTriggerCreate
from app.schemas.common import ResponseModel
from app.workers.monitoring_tasks import execute_monitoring_job
from app.services.workflows.events import EventBus

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

@router.post("/run", response_model=ResponseModel)
async def run_monitoring_job(
    request: MonitoringJobCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Trigger a manual model monitoring drift job."""
    baseline = await db.get(MonitoringBaseline, request.baseline_id)
    if not baseline:
        raise HTTPException(status_code=404, detail="Baseline not found")
        
    job = MonitoringJob(
        model_version_id=request.model_version_id,
        baseline_id=request.baseline_id,
        window_start=request.window_start,
        window_end=request.window_end,
        status="pending"
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Dispatch Celery worker
    execute_monitoring_job.delay(str(job.id))
    
    return ResponseModel(
        message="Monitoring job triggered successfully",
        data={"job": MonitoringJobResponse.from_orm(job)}
    )

@router.get("/reports", response_model=ResponseModel)
async def list_drift_reports(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """List recent data drift reports."""
    stmt = select(DriftReport).order_by(DriftReport.created_at.desc()).offset(offset).limit(limit)
    reports = (await db.execute(stmt)).scalars().all()
    
    return ResponseModel(
        message="Drift reports retrieved",
        data={"reports": [DriftReportResponse.from_orm(r) for r in reports]}
    )

@router.get("/models/{model_version_id}/reports", response_model=ResponseModel)
async def get_model_drift_reports(
    model_version_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get drift reports for a specific model."""
    stmt = (
        select(DriftReport)
        .join(MonitoringJob)
        .where(MonitoringJob.model_version_id == model_version_id)
        .order_by(DriftReport.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    reports = (await db.execute(stmt)).scalars().all()
    
    return ResponseModel(
        message="Model drift reports retrieved",
        data={"reports": [DriftReportResponse.from_orm(r) for r in reports]}
    )

@router.post("/retrain", response_model=ResponseModel)
async def trigger_retraining(
    request: RetrainTriggerCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Manually trigger a retraining workflow for a model."""
    await EventBus.publish(db, "MANUAL_RETRAINING_TRIGGERED", payload={
        "model_version_id": str(request.model_version_id),
        "reason": request.reason,
        "triggered_by": str(current_user.id)
    })
    
    return ResponseModel(
        message="Retraining workflow triggered",
        data={"model_version_id": str(request.model_version_id)}
    )
