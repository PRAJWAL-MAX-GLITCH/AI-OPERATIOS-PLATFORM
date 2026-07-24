"""
Workflow API Router
===================
Endpoints for Enterprise AI Workflow Orchestration.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.models.domain import User
from app.models.workflow import WorkflowDefinition, WorkflowRun, TaskRun
from app.schemas.workflows import (
    WorkflowDefinitionCreate, 
    WorkflowDefinitionResponse, 
    WorkflowRunCreate, 
    WorkflowRunResponse
)
from app.schemas.common import ResponseModel
from app.workers.workflow_tasks import orchestrate_workflow

router = APIRouter(prefix="/workflows", tags=["Workflows"])

@router.post("", response_model=ResponseModel)
async def create_workflow_definition(
    request: WorkflowDefinitionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Register a new workflow definition."""
    # Check if exists
    stmt = select(WorkflowDefinition).where(WorkflowDefinition.name == request.name)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Workflow with this name already exists")
        
    workflow = WorkflowDefinition(
        name=request.name,
        description=request.description,
        dag_definition=request.dag_definition.dict(by_alias=True),
        default_parameters=request.default_parameters
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    return ResponseModel(
        message="Workflow definition created successfully",
        data={"workflow": WorkflowDefinitionResponse.from_orm(workflow)}
    )

@router.get("", response_model=ResponseModel)
async def list_workflow_definitions(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """List all available workflow definitions."""
    stmt = select(WorkflowDefinition)
    workflows = (await db.execute(stmt)).scalars().all()
    
    return ResponseModel(
        message="Workflow definitions retrieved",
        data={"workflows": [WorkflowDefinitionResponse.from_orm(w) for w in workflows]}
    )

@router.post("/{workflow_id}/run", response_model=ResponseModel)
async def run_workflow(
    workflow_id: uuid.UUID,
    request: WorkflowRunCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Trigger a workflow run."""
    definition = await db.get(WorkflowDefinition, workflow_id)
    if not definition:
        raise HTTPException(status_code=404, detail="Workflow definition not found")
        
    from datetime import datetime, timezone
    
    run = WorkflowRun(
        workflow_id=definition.id,
        status="pending",
        parameters=request.parameters,
        project_id=request.project_id,
        started_at=datetime.now(timezone.utc)
    )
    db.add(run)
    await db.flush()
    
    # Instantiate tasks
    tasks_def = definition.dag_definition.get("tasks", [])
    for t_def in tasks_def:
        task_run = TaskRun(
            workflow_run_id=run.id,
            task_id=t_def["id"],
            task_type=t_def["type"],
            status="pending"
        )
        db.add(task_run)
        
    await db.commit()
    
    # Dispatch
    orchestrate_workflow.delay(str(run.id))
    
    return ResponseModel(
        message="Workflow run triggered successfully",
        data={"run_id": str(run.id)}
    )

@router.get("/runs/{run_id}", response_model=ResponseModel)
async def get_workflow_run_status(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get the status of a specific workflow execution, including all tasks."""
    stmt = select(WorkflowRun).options(selectinload(WorkflowRun.tasks)).where(WorkflowRun.id == run_id)
    run = (await db.execute(stmt)).scalars().first()
    
    if not run:
        raise HTTPException(status_code=404, detail="Workflow run not found")
        
    return ResponseModel(
        message="Workflow run status retrieved",
        data={"run": WorkflowRunResponse.from_orm(run)}
    )

@router.get("/history", response_model=ResponseModel)
async def get_workflow_history(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get the history of all workflow executions."""
    stmt = select(WorkflowRun).order_by(WorkflowRun.started_at.desc()).offset(offset).limit(limit)
    runs = (await db.execute(stmt)).scalars().all()
    
    return ResponseModel(
        message="Workflow history retrieved",
        data={"runs": [WorkflowRunResponse.from_orm(r) for r in runs]}
    )
