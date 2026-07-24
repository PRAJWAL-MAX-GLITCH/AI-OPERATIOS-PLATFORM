"""
Celery Workers for Workflow Orchestration
"""
import asyncio
import uuid
import structlog
from celery import shared_task
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.workflow import WorkflowRun, TaskRun
from app.services.workflows.core.engine import DAGParser
from app.services.workflows.tasks.executor import TaskExecutor

logger = structlog.get_logger(__name__)

@shared_task(name="orchestrate_workflow")
def orchestrate_workflow(workflow_run_id_str: str):
    """
    Evaluates the DAG and dispatches ready tasks. 
    Runs every time a task completes or the workflow starts.
    """
    async def _run():
        workflow_run_id = uuid.UUID(workflow_run_id_str)
        async with AsyncSessionLocal() as db:
            run = await db.get(WorkflowRun, workflow_run_id)
            if not run or run.status not in ["pending", "running"]:
                return

            if run.status == "pending":
                run.status = "running"
                await db.commit()

            # Fetch all tasks for this run
            stmt = select(TaskRun).where(TaskRun.workflow_run_id == workflow_run_id)
            result = await db.execute(stmt)
            tasks = result.scalars().all()

            # Check for failure
            if any(t.status == "failed" for t in tasks):
                run.status = "failed"
                run.error_message = "A task failed in the workflow."
                await db.commit()
                return

            # Check for completion
            if all(t.status == "completed" for t in tasks):
                run.status = "completed"
                await db.commit()
                return

            # Find ready tasks
            completed_tasks = {t.task_id for t in tasks if t.status == "completed"}
            dag = DAGParser.parse_dag(run.definition.dag_definition)
            ready_task_ids = DAGParser.get_ready_tasks(dag, completed_tasks)

            # Dispatch ready tasks that are pending
            for t in tasks:
                if t.task_id in ready_task_ids and t.status == "pending":
                    execute_workflow_task.delay(str(t.id))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_run())


@shared_task(name="execute_workflow_task")
def execute_workflow_task(task_run_id_str: str):
    """Executes a specific task run and then triggers the orchestrator."""
    async def _run():
        task_run_id = uuid.UUID(task_run_id_str)
        async with AsyncSessionLocal() as db:
            await TaskExecutor.execute_task(db, task_run_id)
            
            # Fetch to get workflow ID to re-trigger orchestration
            task_run = await db.get(TaskRun, task_run_id)
            if task_run:
                orchestrate_workflow.delay(str(task_run.workflow_run_id))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_run())
