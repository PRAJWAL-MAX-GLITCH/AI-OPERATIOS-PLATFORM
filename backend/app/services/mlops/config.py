"""
MLOps Configuration and Initialization
======================================
Sets up MLflow tracking URI and artifacts location.
"""
from __future__ import annotations
import os
import mlflow
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)

# Base directory for the backend app
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MLFLOW_DB = BASE_DIR / "data" / "mlflow.db"
MLFLOW_ARTIFACTS = BASE_DIR / "data" / "mlruns"

TRACKING_URI = f"sqlite:///{MLFLOW_DB.as_posix()}"

def init_mlflow():
    """Initialize MLflow configuration."""
    MLFLOW_ARTIFACTS.mkdir(parents=True, exist_ok=True)
    mlflow.set_tracking_uri(TRACKING_URI)
    logger.info("mlflow_initialized", tracking_uri=TRACKING_URI)
