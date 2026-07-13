"""
Model Loader with LRU Cache
===========================
Caches loaded models and preprocessing pipelines in memory to optimize latency.
"""
from __future__ import annotations
import mlflow
import structlog
from typing import Any, Tuple
from functools import lru_cache

from app.services.mlops.config import init_mlflow
from app.services.mlops.model_registry import model_registry

logger = structlog.get_logger(__name__)
init_mlflow()


class ModelLoader:

    @staticmethod
    @lru_cache(maxsize=10)
    def load_model(model_name: str, version: str) -> Any:
        """
        Loads the MLflow model into memory and caches it.
        Uses LRU Cache to keep up to 10 active models in memory.
        """
        logger.info("loading_model_from_mlflow", model_name=model_name, version=version)
        
        # Load the model using sklearn flavor to retain predict_proba and shap compatibility
        model_uri = f"models:/{model_name}/{version}"
        model = mlflow.sklearn.load_model(model_uri)
        return model

    @staticmethod
    def get_version(model_name: str, version: str = None) -> str:
        """
        Resolves the correct version string. 
        If version is None, attempts to find the "Production" stage model, else latest.
        """
        if version:
            return version
            
        versions = model_registry.get_latest_versions(model_name, stages=["Production"])
        if versions:
            return versions[0]["version"]
            
        # Fallback to absolute latest if no production model
        versions = model_registry.get_latest_versions(model_name)
        if not versions:
            raise ValueError(f"No registered versions found for model '{model_name}'.")
            
        return versions[0]["version"]


model_loader = ModelLoader()
