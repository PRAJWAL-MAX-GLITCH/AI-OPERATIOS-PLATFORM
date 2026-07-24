"""
Workflow Event System
=====================
Handles triggering workflows based on system events.
"""
import uuid
import structlog
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.models.workflow import WorkflowEvent, WorkflowDefinition, WorkflowRun, TaskRun
from app.services.workflows.core.engine import DAGParser
from app.workers.workflow_tasks import orchestrate_workflow

logger = structlog.get_logger(__name__)

class EventBus:
    """System event bus for triggering workflow automation."""

    @staticmethod
    async def publish(db: AsyncSession, event_type: str, payload: Dict[str, Any]):
        """Publish an event to the database and trigger related workflows."""
        event = WorkflowEvent(
            event_type=event_type,
            payload=payload,
            status="pending"
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        
        logger.info("event_published", event_type=event_type, event_id=str(event.id))
        
        try:
            # Here we would normally look up bindings for this event
            # For simplicity in this implementation, we will match specific hardcoded workflows
            await EventBus._evaluate_triggers(db, event)
            event.status = "processed"
        except Exception as e:
            logger.error("event_processing_failed", exc_info=True)
            event.status = "failed"
            event.error_message = str(e)
            
        event.processed_at = datetime.now(timezone.utc)
        await db.commit()

    @staticmethod
    async def _evaluate_triggers(db: AsyncSession, event: WorkflowEvent):
        """Evaluate if the event triggers any workflows and start them."""
        # This is a simplified rule engine. In a full system, you would query
        # a `WorkflowTriggers` table.
        from sqlalchemy import select
        
        target_workflow_name = None
        if event.event_type == "DATASET_UPLOADED":
            target_workflow_name = "validation_pipeline"
        elif event.event_type == "TRAINING_COMPLETED":
            target_workflow_name = "evaluation_pipeline"
            
        if not target_workflow_name:
            return
            
        stmt = select(WorkflowDefinition).where(WorkflowDefinition.name == target_workflow_name)
        result = await db.execute(stmt)
        definition = result.scalars().first()
        
        if definition:
            await EventBus._start_workflow(db, definition, event.payload)

    @staticmethod
    async def _start_workflow(db: AsyncSession, definition: WorkflowDefinition, parameters: Dict[str, Any]):
        """Create a new WorkflowRun and its Tasks from the Definition."""
        run = WorkflowRun(
            workflow_id=definition.id,
            status="pending",
            parameters=parameters,
            started_at=datetime.now(timezone.utc)
        )
        db.add(run)
        await db.flush()
        
        # Instantiate TaskRuns from DAG
        tasks_definition = definition.dag_definition.get("tasks", [])
        for t_def in tasks_definition:
            task_run = TaskRun(
                workflow_run_id=run.id,
                task_id=t_def["id"],
                task_type=t_def["type"],
                status="pending"
            )
            db.add(task_run)
            
        await db.commit()
        
        # Dispatch to celery orchestrator
        orchestrate_workflow.delay(str(run.id))
        logger.info("workflow_triggered_from_event", run_id=str(run.id), workflow=definition.name)
