"""
Training Service
================
Orchestrates: load dataset → run preprocessing (from latest report) → run training → save model & metadata.
"""
from __future__ import annotations
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.training import TrainingJob
from app.services.dataset import dataset_service
from app.services.storage import storage_service
from app.services.dataset_parser import parse_file
from app.services.preprocessing_service import preprocessing_service
from app.services.preprocessing.pipeline import run_preprocessing_pipeline
from app.services.preprocessing.config import PipelineConfig

from app.schemas.training import TrainingRequest
from app.services.training.config import TrainingConfig, SplitConfig
from app.services.training.pipeline import run_training_pipeline
from app.services.training.serializer import save_model
from app.core.exceptions import ForbiddenError, ResourceNotFoundError

logger = structlog.get_logger(__name__)


class TrainingService:

    async def start_training(
        self,
        db: AsyncSession,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        request: TrainingRequest,
    ) -> TrainingJob:
        """
        Runs the training pipeline asynchronously (mocked as sync for now, wrapped).
        Requires a successfully preprocessed dataset.
        """
        dataset = await dataset_service.get_dataset_or_404(db, dataset_id)

        # ── Preprocessing Gate ───────────────────────────────────── #
        try:
            prep_report = await preprocessing_service.get_latest_report(db, dataset_id)
        except ResourceNotFoundError:
            raise ForbiddenError(
                "Dataset has not been preprocessed. "
                "Run POST /datasets/{id}/preprocess before training."
            )

        # ── Persist Initial Job ────────────────────────────────── #
        job = TrainingJob(
            dataset_id=dataset.id,
            project_id=project_id,
            status="running",
            algorithm=request.algorithm,
            problem_type=request.problem_type,
            target_column=request.target_column,
            parameters=request.parameters,
            preprocessing_pipeline_path=prep_report.pipeline_path
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info("training_job_started", dataset_id=str(dataset_id), job_id=str(job.id))

        try:
            # 1. Load Raw Dataset
            content = await storage_service.read(dataset.storage_path)
            raw_df  = parse_file(content, dataset.original_filename)

            # 2. Apply Preprocessing
            if not prep_report.report or "config" not in prep_report.report:
                raise ValueError("Preprocessing config missing from report.")
            
            prep_cfg_dict = prep_report.report["config"]
            prep_cfg = PipelineConfig(**prep_cfg_dict)
            
            # The preprocessing pipeline fits and transforms
            processed_df, _ = run_preprocessing_pipeline(raw_df, prep_cfg, dataset_name=dataset.name)
            
            # 3. Configure Training
            cfg = TrainingConfig(
                problem_type=request.problem_type,
                target_column=request.target_column,
                algorithm=request.algorithm,
                split=SplitConfig(
                    test_size=request.test_size,
                    random_state=request.random_state
                ),
                parameters=request.parameters
            )

            # 4. Run Training
            result = run_training_pipeline(processed_df, cfg, dataset_name=dataset.name)
            
            if result.errors:
                raise RuntimeError(f"Training pipeline errors: {result.errors}")

            # 5. Save Model
            metadata = {
                "algorithm": result.algorithm,
                "problem_type": result.problem_type,
                "metrics": result.metrics,
                "config": result.config
            }
            model_path = save_model(result.model, str(dataset_id), str(project_id), metadata)

            job.status     = "completed"
            job.model_path = model_path
            job.metrics    = result.metrics
            
            logger.info(
                "training_job_completed",
                job_id=str(job.id),
                metrics=result.metrics,
            )
        except Exception as exc:
            job.status        = "failed"
            job.error_message = str(exc)
            logger.error("training_job_failed", job_id=str(job.id), error=str(exc))

        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def get_job(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
    ) -> TrainingJob:
        query = select(TrainingJob).where(TrainingJob.id == job_id)
        result = await db.execute(query)
        job = result.scalars().first()
        if not job:
            raise ResourceNotFoundError(f"Training job {job_id} not found.")
        return job

    async def get_jobs_for_dataset(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> list[TrainingJob]:
        query = (
            select(TrainingJob)
            .where(TrainingJob.dataset_id == dataset_id)
            .order_by(TrainingJob.created_at.desc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())


training_service = TrainingService()
