"""
Task Executor
=============
Base classes for tasks that execute within workflows.
"""
from typing import Dict, Any, Callable
import structlog
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import TaskRun, WorkflowRun

logger = structlog.get_logger(__name__)

class TaskExecutor:
    """Registry and execution interface for workflow tasks."""
    
    _task_handlers: Dict[str, Callable] = {}

    @classmethod
    def register_task(cls, task_type: str):
        """Decorator to register a task handler."""
        def decorator(func: Callable):
            cls._task_handlers[task_type] = func
            return func
        return decorator

    @classmethod
    async def execute_task(cls, db: AsyncSession, task_run_id: str) -> None:
        """Executes a specific task run and handles retries and failures."""
        task_run = await db.get(TaskRun, task_run_id)
        if not task_run:
            logger.error("task_run_not_found", task_run_id=task_run_id)
            return

        task_run.status = "running"
        task_run.started_at = datetime.now(timezone.utc)
        await db.commit()

        handler = cls._task_handlers.get(task_run.task_type)
        if not handler:
            task_run.status = "failed"
            task_run.error_message = f"No handler registered for task type: {task_run.task_type}"
            task_run.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return

        try:
            # Execute handler
            output = await handler(task_run.input_data)
            task_run.output_data = output or {}
            task_run.status = "completed"
        except Exception as e:
            logger.error("task_execution_failed", task_run_id=task_run_id, exc_info=True)
            task_run.retries += 1
            if task_run.retries >= task_run.max_retries:
                task_run.status = "failed"
                task_run.error_message = str(e)
            else:
                task_run.status = "pending" # Requeue
        finally:
            if task_run.status in ["completed", "failed"]:
                task_run.completed_at = datetime.now(timezone.utc)
            
            await db.commit()

        # If completed, we should trigger the engine to check for next tasks
        # (This is handled by the celery orchestrator loop)
