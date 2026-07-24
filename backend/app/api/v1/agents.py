"""
Agent API Router
================
Endpoints for interacting with the Enterprise AI Agent Platform.
"""
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import get_db_session
from app.api.dependencies import get_current_user
from app.models.domain import User
from app.models.agent import AgentTask, AgentRun, AgentMessage
from app.schemas.agents import AgentRunRequest, AgentTaskResponse, AgentRunStatusResponse, AgentHistoryResponse
from app.schemas.common import ResponseModel
from app.services.agents.core.registry import AgentRegistry
from app.services.agents.orchestration.orchestrator import TaskOrchestrator
from app.services.agents.memory.manager import AgentMemoryManager
from app.workers.agent_tasks import run_agent_task

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("", response_model=ResponseModel)
async def list_available_agents():
    """List all registered autonomous agents."""
    # Ensure they are imported and registered
    from app.services.agents.impl import agents  # noqa
    
    return ResponseModel(
        message="Available agents retrieved",
        data={"agents": AgentRegistry.list_agents()}
    )


@router.post("/run", response_model=ResponseModel)
async def run_agent_sync(
    request: AgentRunRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Execute an agent synchronously. Good for quick tasks.
    Blocks until the agent finishes or times out.
    """
    from app.services.agents.impl import agents  # noqa
    
    if request.agent_type not in AgentRegistry.list_agents():
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")

    # Create task record
    task = AgentTask(
        user_id=current_user.id,
        project_id=request.project_id,
        agent_type=request.agent_type,
        title=request.task_title,
        description=request.task_description,
        status="pending"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Run orchestrator
    run = await TaskOrchestrator.run_task_sync(db, task.id, request.agent_type)
    
    # Refresh task
    await db.refresh(task)

    return ResponseModel(
        message="Agent executed successfully" if task.status == "completed" else "Agent execution failed",
        data={
            "task_id": str(task.id),
            "run_id": str(run.id),
            "status": task.status,
            "result": task.result,
            "error_message": task.error_message
        }
    )


@router.post("/task", response_model=ResponseModel)
async def enqueue_agent_task(
    request: AgentRunRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    Enqueue an agent task for background execution via Celery.
    Returns immediately with a task_id to poll status.
    """
    from app.services.agents.impl import agents  # noqa
    
    if request.agent_type not in AgentRegistry.list_agents():
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")

    # Create task record
    task = AgentTask(
        user_id=current_user.id,
        project_id=request.project_id,
        agent_type=request.agent_type,
        title=request.task_title,
        description=request.task_description,
        status="pending"
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Dispatch to Celery
    celery_job = run_agent_task.delay(str(task.id), request.agent_type)
    
    task.celery_task_id = celery_job.id
    await db.commit()

    return ResponseModel(
        message="Agent task enqueued successfully",
        data={"task_id": str(task.id), "celery_task_id": celery_job.id}
    )


@router.get("/tasks/{task_id}", response_model=ResponseModel)
async def get_task_status(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Check the status and result of an agent task."""
    task = await db.get(AgentTask, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    return ResponseModel(
        message="Task status retrieved",
        data={
            "task_id": str(task.id),
            "status": task.status,
            "result": task.result,
            "error_message": task.error_message
        }
    )


@router.get("/history/{task_id}", response_model=ResponseModel)
async def get_task_history(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Get the multi-agent conversation history and tool outputs for a task."""
    task = await db.get(AgentTask, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    history = await AgentMemoryManager.get_task_history(db, task_id, limit=100)
    
    return ResponseModel(
        message="Task history retrieved",
        data={"messages": history}
    )


@router.get("/tasks", response_model=ResponseModel)
async def list_user_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    agent_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """List all agent tasks submitted by the current user, newest first."""
    stmt = (
        select(AgentTask)
        .where(AgentTask.user_id == current_user.id)
        .order_by(desc(AgentTask.created_at))
        .limit(limit)
        .offset(offset)
    )
    if status_filter:
        stmt = stmt.where(AgentTask.status == status_filter)
    if agent_type:
        stmt = stmt.where(AgentTask.agent_type == agent_type)

    result = await db.execute(stmt)
    tasks = result.scalars().all()

    return ResponseModel(
        message="Tasks retrieved",
        data={
            "tasks": [
                {
                    "task_id": str(t.id),
                    "agent_type": t.agent_type,
                    "title": t.title,
                    "description": t.description,
                    "status": t.status,
                    "error_message": t.error_message,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "updated_at": t.updated_at.isoformat() if t.updated_at else None,
                }
                for t in tasks
            ],
            "total": len(tasks),
        }
    )


@router.post("/tasks/{task_id}/cancel", response_model=ResponseModel)
async def cancel_task(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Cancel a pending or running agent task."""
    task = await db.get(AgentTask, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status not in ("pending", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a task with status '{task.status}'"
        )

    task.status = "cancelled"
    task.error_message = "Cancelled by user."
    await db.commit()

    return ResponseModel(
        message="Task cancelled",
        data={"task_id": str(task.id), "status": "cancelled"}
    )


@router.get("/tasks/{task_id}/runs", response_model=ResponseModel)
async def get_task_runs(
    task_id: uuid.UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """List all agent run records for a task, with their messages."""
    task = await db.get(AgentTask, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Task not found")

    stmt = select(AgentRun).where(AgentRun.task_id == task_id).order_by(AgentRun.created_at)
    result = await db.execute(stmt)
    runs = result.scalars().all()

    run_data = []
    for run in runs:
        msgs_stmt = select(AgentMessage).where(AgentMessage.run_id == run.id).order_by(AgentMessage.step_index)
        msgs_result = await db.execute(msgs_stmt)
        messages = msgs_result.scalars().all()
        run_data.append({
            "run_id": str(run.id),
            "agent_type": run.agent_type,
            "status": run.status,
            "started_at": run.started_at,
            "completed_at": run.completed_at,
            "duration_ms": run.duration_ms,
            "steps_taken": run.steps_taken,
            "tools_used": run.tools_used,
            "final_output": run.final_output,
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "tool_name": m.tool_name,
                    "tool_input": m.tool_input,
                    "tool_output": m.tool_output,
                    "step_index": m.step_index,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                }
                for m in messages
            ],
        })

    return ResponseModel(
        message="Runs retrieved",
        data={"runs": run_data}
    )
