"""
MLflow Model Registry
=====================
Manages model versions and stages (Staging, Production, etc.).
"""
from __future__ import annotations
import mlflow
from mlflow.tracking import MlflowClient
import structlog
from typing import Any

from app.services.mlops.config import init_mlflow

logger = structlog.get_logger(__name__)

init_mlflow()
client = MlflowClient()


class ModelRegistry:

    @staticmethod
    def register_model(run_id: str, model_name: str) -> mlflow.entities.model_registry.ModelVersion:
        """
        Registers a model run into the MLflow model registry.
        """
        model_uri = f"runs:/{run_id}/model"
        mv = mlflow.register_model(model_uri, model_name)
        logger.info("model_registered", name=model_name, version=mv.version)
        return mv

    @staticmethod
    def transition_stage(model_name: str, version: str, stage: str, archive_existing: bool = True) -> None:
        """
        Transitions a model version to a new stage (e.g. Staging, Production).
        Valid stages: 'None', 'Staging', 'Production', 'Archived'
        """
        client.transition_model_version_stage(
            name=model_name,
            version=version,
            stage=stage,
            archive_existing_versions=archive_existing
        )
        logger.info("model_stage_transitioned", name=model_name, version=version, stage=stage)

    @staticmethod
    def get_latest_versions(model_name: str, stages: list[str] = None) -> list[dict[str, Any]]:
        """
        Gets the latest versions of a registered model.
        """
        versions = client.get_latest_versions(name=model_name, stages=stages)
        return [
            {
                "name": v.name,
                "version": v.version,
                "current_stage": v.current_stage,
                "status": v.status,
                "run_id": v.run_id
            }
            for v in versions
        ]
        
    @staticmethod
    def get_registered_models() -> list[dict[str, Any]]:
        """List all registered models."""
        models = client.search_registered_models()
        res = []
        for m in models:
            latest = [
                {"version": v.version, "stage": v.current_stage, "run_id": v.run_id} 
                for v in m.latest_versions
            ]
            res.append({
                "name": m.name,
                "latest_versions": latest,
                "creation_timestamp": m.creation_timestamp,
                "last_updated_timestamp": m.last_updated_timestamp,
            })
        return res


model_registry = ModelRegistry()
