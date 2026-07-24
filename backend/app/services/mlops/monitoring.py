"""
Model Monitoring Orchestrator
=============================
Triggers drift detection jobs, coordinates with the workflow engine, and dispatches alerts.
"""
import uuid
import pandas as pd
import numpy as np
import structlog
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.monitoring import MonitoringJob, DriftReport, MonitoringBaseline
from app.services.mlops.drift import DriftDetector
from app.services.observability.alerts import AlertManager
from app.services.workflows.events import EventBus

logger = structlog.get_logger(__name__)

class MonitoringOrchestrator:

    @staticmethod
    async def execute_job(db: AsyncSession, job_id: uuid.UUID):
        """Execute a single monitoring job."""
        job = await db.get(MonitoringJob, job_id)
        if not job or job.status != "pending":
            return
            
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await db.commit()
        
        try:
            baseline = await db.get(MonitoringBaseline, job.baseline_id)
            if not baseline:
                raise ValueError(f"Baseline not found for job {job_id}")

            # In a real environment, we would pull predictions from `PredictionLog` 
            # within the job window. Here we simulate the pulled data to demonstrate drift.
            
            # Simulated drift detection logic
            # Imagine we have `production_data` (a Pandas DataFrame) and `baseline_stats`
            production_data = MonitoringOrchestrator._get_simulated_production_data()
            baseline_data = MonitoringOrchestrator._get_simulated_baseline_data()
            
            feature_drift_details = {}
            total_drift_features = 0
            
            for feature in ["age", "income", "score"]:
                res = DriftDetector.evaluate_numerical_feature(
                    expected=baseline_data[feature].values,
                    actual=production_data[feature].values
                )
                feature_drift_details[feature] = res
                if res["has_drift"]:
                    total_drift_features += 1
            
            overall_drift_score = total_drift_features / len(feature_drift_details)
            has_data_drift = bool(overall_drift_score >= 0.3) # 30% features drifted
            
            report = DriftReport(
                job_id=job.id,
                overall_drift_score=overall_drift_score,
                has_data_drift=str(has_data_drift).lower(),
                has_prediction_drift="false",
                feature_drift_details=feature_drift_details,
                performance_metrics={}
            )
            db.add(report)
            
            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
            
            # 1. Trigger Alert if drifted
            if has_data_drift:
                AlertManager.alert(
                    level="WARNING",
                    title=f"Data Drift Detected (Score: {overall_drift_score:.2f})",
                    message=f"Model Version {job.model_version_id} has exceeded the drift threshold."
                )
                
                # 2. Trigger Retraining Workflow via EventBus
                await EventBus.publish(db, "HIGH_DRIFT_DETECTED", payload={
                    "model_version_id": str(job.model_version_id),
                    "drift_score": overall_drift_score,
                    "report_id": str(report.id)
                })
                
        except Exception as e:
            logger.error("monitoring_job_failed", job_id=str(job_id), error=str(e), exc_info=True)
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

    @staticmethod
    def _get_simulated_production_data() -> pd.DataFrame:
        """Simulates production prediction input data with slight drift."""
        np.random.seed(42)
        return pd.DataFrame({
            "age": np.random.normal(35, 12, 1000), # Mean 35, std 12
            "income": np.random.normal(60000, 20000, 1000), # Mean 60k
            "score": np.random.normal(0.4, 0.2, 1000)
        })

    @staticmethod
    def _get_simulated_baseline_data() -> pd.DataFrame:
        """Simulates the baseline data."""
        np.random.seed(10)
        return pd.DataFrame({
            "age": np.random.normal(32, 10, 1000), # Mean 32, std 10
            "income": np.random.normal(55000, 15000, 1000), # Mean 55k
            "score": np.random.normal(0.5, 0.1, 1000)
        })
