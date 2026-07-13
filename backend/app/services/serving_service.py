"""
Serving Service
===============
Coordinates HTTP payload, pipeline execution, and database logging.
"""
from __future__ import annotations
import uuid
import time
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.serving import PredictionLog
from app.schemas.serving import PredictRequest
from app.services.serving.model_loader import model_loader
from app.services.serving.prediction_pipeline import run_prediction_pipeline
from app.core.exceptions import ResourceNotFoundError

logger = structlog.get_logger(__name__)


class ServingService:

    async def predict_online(
        self,
        db: AsyncSession,
        project_id: uuid.UUID,
        model_name: str,
        request: PredictRequest
    ) -> PredictionLog:
        """
        Executes a single online prediction and logs it to the database.
        """
        start_time = time.perf_counter()
        
        try:
            # Resolve correct version
            version = model_loader.get_version(model_name, request.version)
            
            # Execute Pipeline
            prediction, confidence, explanation = run_prediction_pipeline(
                model_name=model_name,
                version=version,
                payload=request.features,
                explain=request.explain
            )
            
            latency_ms = (time.perf_counter() - start_time) * 1000
            
            # Log Prediction
            log_entry = PredictionLog(
                project_id=project_id,
                model_name=model_name,
                model_version=version,
                latency_ms=latency_ms,
                confidence=confidence,
                input_payload=request.features,
                prediction_result=prediction.tolist() if hasattr(prediction, "tolist") else prediction,
                explanation=explanation
            )
            db.add(log_entry)
            await db.commit()
            await db.refresh(log_entry)
            
            logger.info("prediction_successful", model=model_name, version=version, latency=latency_ms)
            return log_entry
            
        except Exception as exc:
            logger.error("prediction_failed", model=model_name, error=str(exc))
            raise

    async def get_prediction_history(
        self,
        db: AsyncSession,
        project_id: uuid.UUID,
        model_name: str,
        limit: int = 100
    ) -> list[PredictionLog]:
        """Fetch history of predictions for a given model."""
        query = (
            select(PredictionLog)
            .where(
                PredictionLog.project_id == project_id,
                PredictionLog.model_name == model_name
            )
            .order_by(PredictionLog.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())


serving_service = ServingService()
