"""
Evaluation Service
==================
Orchestrates: dataset validation → automl evaluation pipeline → model persistence.
"""
from __future__ import annotations
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.evaluation import EvaluationJob
from app.services.dataset import dataset_service
from app.services.storage import storage_service
from app.services.dataset_parser import parse_file
from app.services.preprocessing_service import preprocessing_service
from app.services.preprocessing.pipeline import run_preprocessing_pipeline
from app.services.preprocessing.config import PipelineConfig

from app.schemas.evaluation import EvaluationRequest
from app.services.evaluation.config import AutoMLConfig, CVConfig
from app.services.evaluation.automl_pipeline import run_automl_pipeline
from app.services.training.serializer import save_model
from app.services.mlops.experiment_tracker import experiment_tracker
from app.services.mlops.model_registry import model_registry
from app.core.exceptions import ForbiddenError, ResourceNotFoundError

logger = structlog.get_logger(__name__)


class EvaluationService:

    async def start_evaluation(
        self,
        db: AsyncSession,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        request: EvaluationRequest,
    ) -> EvaluationJob:
        """
        Runs the AutoML evaluation pipeline.
        Requires a successfully preprocessed dataset.
        """
        dataset = await dataset_service.get_dataset_or_404(db, dataset_id)

        # ── Preprocessing Gate ───────────────────────────────────── #
        try:
            prep_report = await preprocessing_service.get_latest_report(db, dataset_id)
        except ResourceNotFoundError:
            raise ForbiddenError(
                "Dataset has not been preprocessed. "
                "Run POST /datasets/{id}/preprocess before evaluation."
            )

        # ── Persist Initial Job ────────────────────────────────── #
        job = EvaluationJob(
            dataset_id=dataset.id,
            project_id=project_id,
            status="running",
            problem_type=request.problem_type,
            target_column=request.target_column,
            preprocessing_pipeline_path=prep_report.pipeline_path
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info("evaluation_job_started", dataset_id=str(dataset_id), job_id=str(job.id))

        try:
            # 1. Load Raw Dataset & Apply Preprocessing
            content = await storage_service.read(dataset.storage_path)
            raw_df  = parse_file(content, dataset.original_filename)

            if not prep_report.report or "config" not in prep_report.report:
                raise ValueError("Preprocessing config missing from report.")
            
            prep_cfg = PipelineConfig(**prep_report.report["config"])
            processed_df, _ = run_preprocessing_pipeline(raw_df, prep_cfg, dataset_name=dataset.name)
            
            # 2. Configure AutoML
            cfg = AutoMLConfig(
                problem_type=request.problem_type,
                target_column=request.target_column,
                algorithms=request.algorithms,
                primary_metric=request.primary_metric or "",
                cv=CVConfig(folds=request.cv_folds, random_state=request.random_state)
            )

            # 3. Run AutoML Pipeline
            result = run_automl_pipeline(processed_df, cfg, dataset_name=dataset.name)
            
            # 4. Save Best Model
            metadata = {
                "algorithm": result["best_algorithm"],
                "problem_type": request.problem_type,
                "metrics": result["best_metrics"],
                "is_automl": True,
            }
            model_path = save_model(
                result["best_model_instance"], 
                str(dataset_id), 
                str(project_id), 
                metadata
            )

            # 5. Update DB
            job.status = "completed"
            job.best_algorithm = result["best_algorithm"]
            job.best_metrics = result["best_metrics"]
            job.best_model_path = model_path
            job.leaderboard = result["leaderboard"]
            job.report = result["report"]
            
            # 6. Log to MLflow
            try:
                best_run_id = None
                for entry in result["leaderboard"]:
                    # MLflow run for each algorithm evaluated
                    run_id = experiment_tracker.log_training_run(
                        project_id=str(project_id),
                        dataset_id=str(dataset_id),
                        dataset_name=dataset.name,
                        algorithm=entry["algorithm"],
                        metrics=entry["metrics"],
                        params={}, # Default params for AutoML
                        model=result["best_model_instance"] if entry["algorithm"] == result["best_algorithm"] else None,
                        run_name=f"AutoML_{entry['algorithm']}"
                    )
                    if entry["algorithm"] == result["best_algorithm"]:
                        best_run_id = run_id
                
                # Register Best Model in MLflow
                if best_run_id:
                    model_name = f"Project_{project_id}_{dataset_id}"
                    model_registry.register_model(best_run_id, model_name)
                    logger.info("mlflow_automl_best_model_registered", model_name=model_name)
                    
            except Exception as mlf_exc:
                logger.warning("mlflow_logging_failed", error=str(mlf_exc))
            
            logger.info("evaluation_job_completed", job_id=str(job.id), best_algo=job.best_algorithm)
            
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
            logger.error("evaluation_job_failed", job_id=str(job.id), error=str(exc))

        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    async def get_job(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
    ) -> EvaluationJob:
        query = select(EvaluationJob).where(EvaluationJob.id == job_id)
        result = await db.execute(query)
        job = result.scalars().first()
        if not job:
            raise ResourceNotFoundError(f"Evaluation job {job_id} not found.")
        return job

    async def get_jobs_for_dataset(
        self,
        db: AsyncSession,
        dataset_id: uuid.UUID,
    ) -> list[EvaluationJob]:
        query = (
            select(EvaluationJob)
            .where(EvaluationJob.dataset_id == dataset_id)
            .order_by(EvaluationJob.created_at.desc())
        )
        result = await db.execute(query)
        return list(result.scalars().all())


evaluation_service = EvaluationService()
