"""
Deep Learning Service
======================
Orchestrates the full DL training pipeline:
CSV → DataLoader → Model → Train → Checkpoint → MLflow → DB.
"""
from __future__ import annotations
import uuid
import numpy as np
import pandas as pd
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.deep_learning import DLTrainingJob
from app.models.domain import Dataset
from app.services.deep_learning.config import get_device, set_seed, get_device_info
from app.services.deep_learning.dataset import build_dataloaders
from app.services.deep_learning.models import DLModelFactory
from app.services.deep_learning.losses import get_loss_function, get_optimizer, get_scheduler
from app.services.deep_learning.trainer import train_model
from app.services.deep_learning.inference import DLInferenceEngine
from app.services.mlops.experiment_tracker import experiment_tracker
from app.core.exceptions import ResourceNotFoundError

logger = structlog.get_logger(__name__)

BASE_DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


class DeepLearningService:

    # ------------------------------------------------------------------
    # Start Training
    # ------------------------------------------------------------------
    async def start_training(
        self,
        db: AsyncSession,
        project_id: uuid.UUID,
        dataset_id: uuid.UUID,
        request: dict,
    ) -> DLTrainingJob:
        """
        Creates a DLTrainingJob record and synchronously executes training.
        (For async/Celery offload, call this from a task worker.)
        """
        # 1. Validate dataset exists
        dataset = await db.get(Dataset, dataset_id)
        if not dataset:
            raise ResourceNotFoundError("Dataset", str(dataset_id))

        target_column = request["target_column"]
        problem_type  = request["problem_type"]
        hyperparams   = request.get("hyperparameters", {})
        total_epochs  = hyperparams.get("epochs", 50)
        batch_size    = hyperparams.get("batch_size", 64)
        val_split     = hyperparams.get("val_split", 0.2)
        seed          = hyperparams.get("seed", 42)
        patience      = hyperparams.get("patience", 10)

        set_seed(seed)

        # 2. Create DB record
        job_dir       = BASE_DATA_DIR / "dl_jobs" / str(uuid.uuid4())
        checkpoint_dir   = str(job_dir / "checkpoints")
        tensorboard_dir  = str(job_dir / "tensorboard")

        job = DLTrainingJob(
            project_id=project_id,
            dataset_id=dataset_id,
            problem_type=problem_type,
            target_column=target_column,
            architecture=hyperparams.get("architecture", "fully_connected"),
            hyperparameters=hyperparams,
            total_epochs=total_epochs,
            checkpoint_dir=checkpoint_dir,
            tensorboard_dir=tensorboard_dir,
            status="running",
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        try:
            # 3. Load dataset CSV
            dataset_path = dataset.file_path  # type: ignore[attr-defined]
            df = pd.read_csv(dataset_path)
            X  = df.drop(columns=[target_column]).select_dtypes(include=[np.number]).values.astype(np.float32)
            y  = df[target_column].values.astype(np.float32)

            n_features  = X.shape[1]
            num_classes = int(y.max()) + 1 if problem_type == "multiclass_classification" else None

            model_cfg = {**hyperparams, "num_classes": num_classes}

            # 4. Build DataLoaders
            train_loader, val_loader = build_dataloaders(X, y, batch_size=batch_size, val_split=val_split, seed=seed)

            # 5. Build Model
            model = DLModelFactory.create(problem_type, n_features, model_cfg)

            # 6. Optimizer / Loss / Scheduler
            device    = get_device()
            criterion = get_loss_function(problem_type, hyperparams)
            optimizer = get_optimizer(model, hyperparams)
            scheduler = get_scheduler(optimizer, hyperparams, total_epochs)

            # 7. Train
            result = train_model(
                model=model,
                train_loader=train_loader,
                val_loader=val_loader,
                criterion=criterion,
                optimizer=optimizer,
                scheduler=scheduler,
                device=device,
                problem_type=problem_type,
                total_epochs=total_epochs,
                checkpoint_dir=checkpoint_dir,
                tensorboard_dir=tensorboard_dir,
                patience=patience,
            )

            # 8. Log to MLflow (best effort — non-blocking)
            try:
                run_id = experiment_tracker.log_training_run(
                    project_id=str(project_id),
                    dataset_id=str(dataset_id),
                    dataset_name=dataset.name,
                    algorithm=f"DL_{problem_type}",
                    metrics=result["final_metrics"],
                    params=hyperparams,
                    model=None,
                    run_name=f"DL_{problem_type}"
                )
                job.mlflow_run_id = run_id
            except Exception as mlf_exc:
                logger.warning("mlflow_dl_logging_failed", error=str(mlf_exc))

            # 9. Update DB record
            job.status           = "completed"
            job.current_epoch    = result["final_metrics"].get("best_epoch", total_epochs)
            job.best_val_loss    = result["final_metrics"].get("best_val_loss")
            job.best_epoch       = result["final_metrics"].get("best_epoch")
            job.best_model_path  = result["best_model_path"]
            job.metrics_history  = result["metrics_history"]
            job.final_metrics    = result["final_metrics"]

            await db.commit()
            await db.refresh(job)

            logger.info("dl_job_completed", job_id=str(job.id))
            return job

        except Exception as exc:
            job.status        = "failed"
            job.error_message = str(exc)
            await db.commit()
            logger.error("dl_job_failed", job_id=str(job.id), error=str(exc))
            raise

    # ------------------------------------------------------------------
    # List Jobs
    # ------------------------------------------------------------------
    async def list_jobs(
        self,
        db: AsyncSession,
        project_id: uuid.UUID,
    ) -> list[DLTrainingJob]:
        result = await db.execute(
            select(DLTrainingJob)
            .where(DLTrainingJob.project_id == project_id)
            .order_by(DLTrainingJob.created_at.desc())
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Get Job
    # ------------------------------------------------------------------
    async def get_job(self, db: AsyncSession, job_id: uuid.UUID) -> DLTrainingJob:
        job = await db.get(DLTrainingJob, job_id)
        if not job:
            raise ResourceNotFoundError("DLTrainingJob", str(job_id))
        return job

    # ------------------------------------------------------------------
    # Online Prediction
    # ------------------------------------------------------------------
    async def predict(
        self,
        db: AsyncSession,
        job_id: uuid.UUID,
        features: dict,
    ) -> dict:
        job = await self.get_job(db, job_id)
        if job.status != "completed":
            raise ValueError(f"Job {job_id} is not completed (status={job.status})")

        X = np.array([list(features.values())], dtype=np.float32)

        hp         = job.hyperparameters or {}
        num_classes = hp.get("num_classes")
        model_cfg  = {**hp, "num_classes": num_classes}

        # We need input_dim; infer from training data shape via n_features in hp or use X
        input_dim   = X.shape[1]

        model, device = DLInferenceEngine.load_model_from_checkpoint(
            checkpoint_path=job.best_model_path,
            problem_type=job.problem_type,
            input_dim=input_dim,
            model_config=model_cfg,
        )
        return DLInferenceEngine.predict(model, device, X, job.problem_type)


dl_service = DeepLearningService()
