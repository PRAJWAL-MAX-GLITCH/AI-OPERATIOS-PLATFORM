"""
Agent Task Orchestrator
=======================
Manages the lifecycle of an AgentTask (start, delegate, complete, fail).
"""
from __future__ import annotations
import uuid
import structlog
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.agent import AgentTask, AgentRun
from app.services.agents.core.registry import AgentRegistry
from app.services.agents.core.state import AgentState, AgentContext
from app.core.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class TaskOrchestrator:
    """Orchestrates agent execution for a given task."""

    @staticmethod
    async def run_task_sync(db: AsyncSession, task_id: uuid.UUID, agent_type: str) -> AgentRun:
        """
        Synchronously execute an agent to accomplish a task.
        In production, long tasks should use Celery, but this is useful for sub-agents or quick jobs.
        """
        # Fetch task
        task = await db.get(AgentTask, task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found.")

        # Create Run record
        run = AgentRun(
            task_id=task.id,
            agent_type=agent_type,
            status="running"
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        # Setup context & state
        context = AgentContext(
            task_id=task.id,
            run_id=run.id,
            user_id=task.user_id,
            project_id=task.project_id,
            task_title=task.title,
            task_description=task.description,
            db_session=db
        )
        state = AgentState(max_steps=settings.AGENT_MAX_STEPS)

        try:
            # Instantiate agent
            agent = AgentRegistry.create(agent_type)
            
            # Execute
            task.status = "running"
            await db.commit()
            
            final_answer = await agent.execute(context, state)
            
            # Update status
            if state.error:
                run.status = "failed"
                task.status = "failed"
                task.error_message = state.error
            else:
                run.status = "completed"
                task.status = "completed"
                task.result = {"answer": final_answer}
                
        except Exception as e:
            logger.error("agent_execution_failed", exc_info=True)
            run.status = "failed"
            task.status = "failed"
            task.error_message = str(e)
            
        run.completed_at = datetime.now(timezone.utc)
        run.total_steps = state.current_step
        run.state = {"scratchpad": state.scratchpad}
        
        await db.commit()
        await db.refresh(run)
        return run
