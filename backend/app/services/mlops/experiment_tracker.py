"""
MLflow Experiment Tracker
=========================
Wrapper for seamlessly logging experiments, metrics, and models.
"""
from __future__ import annotations
import mlflow
import uuid
import tempfile
import structlog
from typing import Any
from pathlib import Path

from app.services.mlops.config import init_mlflow, MLFLOW_ARTIFACTS

logger = structlog.get_logger(__name__)

# Ensure mlflow is initialized when this module is loaded
init_mlflow()


class ExperimentTracker:

    @staticmethod
    def get_or_create_experiment(experiment_name: str) -> str:
        """Returns the MLflow experiment ID."""
        exp = mlflow.get_experiment_by_name(experiment_name)
        if exp:
            return exp.experiment_id
        
        artifact_loc = Path(MLFLOW_ARTIFACTS / experiment_name).as_posix()
        exp_id = mlflow.create_experiment(experiment_name, artifact_location=f"file:///{artifact_loc}")
        return exp_id

    @staticmethod
    def log_training_run(
        project_id: str,
        dataset_id: str,
        dataset_name: str,
        algorithm: str,
        metrics: dict[str, float],
        params: dict[str, Any],
        model: Any,
        run_name: str = None
    ) -> str:
        """
        Logs a single training run to MLflow.
        Returns the MLflow run ID.
        """
        exp_name = f"Project_{project_id}"
        exp_id = ExperimentTracker.get_or_create_experiment(exp_name)
        
        with mlflow.start_run(experiment_id=exp_id, run_name=run_name or algorithm) as run:
            # Tags
            mlflow.set_tag("dataset_id", dataset_id)
            mlflow.set_tag("dataset_name", dataset_name)
            mlflow.set_tag("algorithm", algorithm)
            
            # Params
            mlflow.log_params(params)
            
            # Metrics
            mlflow.log_metrics(metrics)
            
            # Model
            # Assuming scikit-learn models based on our training factory
            mlflow.sklearn.log_model(model, "model")
            
            logger.info("mlflow_run_logged", run_id=run.info.run_id, exp_id=exp_id)
            return run.info.run_id


experiment_tracker = ExperimentTracker()
