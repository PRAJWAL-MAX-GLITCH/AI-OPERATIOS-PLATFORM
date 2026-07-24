"""
Celery Workers for Model Monitoring
"""
import asyncio
import uuid
import structlog
from celery import shared_task

from app.core.database import AsyncSessionLocal
from app.services.mlops.monitoring import MonitoringOrchestrator

logger = structlog.get_logger(__name__)

@shared_task(name="execute_monitoring_job")
def execute_monitoring_job(job_id_str: str):
    """Executes an asynchronous data drift monitoring job."""
    async def _run():
        job_id = uuid.UUID(job_id_str)
        async with AsyncSessionLocal() as db:
            await MonitoringOrchestrator.execute_job(db, job_id)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(_run())
