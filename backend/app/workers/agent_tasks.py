"""
Agent Celery Tasks
==================
Background tasks for asynchronous agent execution.
"""
import asyncio
import uuid
import structlog
from celery import shared_task

from app.core.database import AsyncSessionLocal
from app.services.agents.orchestration.orchestrator import TaskOrchestrator

logger = structlog.get_logger(__name__)


@shared_task(name="run_agent_task", bind=True)
def run_agent_task(self, task_id_str: str, agent_type: str):
    """
    Celery task to run an agent asynchronously.
    """
    logger.info("celery_run_agent_task_started", task_id=task_id_str, agent_type=agent_type)
    
    async def _run():
        task_id = uuid.UUID(task_id_str)
        async with AsyncSessionLocal() as db:
            run = await TaskOrchestrator.run_task_sync(db, task_id, agent_type)
            return run.status

    # Run the async loop
    loop = asyncio.get_event_loop()
    status = loop.run_until_complete(_run())
    
    return {"status": status, "task_id": task_id_str}
