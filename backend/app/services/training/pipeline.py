"""
Training Pipeline Orchestrator
==============================
Handles data splitting, model training, and evaluation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import pandas as pd
import structlog
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, root_mean_squared_error, mean_absolute_error, r2_score,
    silhouette_score
)

from app.services.training.config import TrainingConfig
from app.services.training.factory import ModelFactory

logger = structlog.get_logger(__name__)


@dataclass
class TrainingResult:
    dataset_name:  str = ""
    config:        dict[str, Any] = field(default_factory=dict)
    algorithm:     str = ""
    problem_type:  str = ""
    metrics:       dict[str, float] = field(default_factory=dict)
    model:         Any = None
    errors:        list[str] = field(default_factory=list)


def run_training_pipeline(
    df: pd.DataFrame,
    cfg: TrainingConfig,
    dataset_name: str = "dataset",
) -> TrainingResult:
    """
    Run the full ML training pipeline.
    Returns TrainingResult containing metrics and the trained model.
    """
    result = TrainingResult(
        dataset_name=dataset_name,
        config=cfg.model_dump(),
        algorithm=cfg.algorithm,
        problem_type=cfg.problem_type
    )

    logger.info("training_started", dataset=dataset_name, algorithm=cfg.algorithm, problem_type=cfg.problem_type)

    try:
        # 1. Prepare data
        if cfg.problem_type in ["classification", "regression"]:
            if not cfg.target_column or cfg.target_column not in df.columns:
                raise ValueError(f"Target column '{cfg.target_column}' is missing or not specified.")
                
            X = df.drop(columns=[cfg.target_column])
            y = df[cfg.target_column]
            
            # 2. Split Data
            stratify = y if cfg.problem_type == "classification" and cfg.split.strategy == "stratified" else None
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, 
                test_size=cfg.split.test_size, 
                random_state=cfg.split.random_state,
                stratify=stratify
            )
            
            # 3. Instantiate & Train Model
            model = ModelFactory.create_model(cfg.problem_type, cfg.algorithm, cfg.parameters)
            model.fit(X_train, y_train)
            result.model = model
            
            # 4. Evaluate
            y_pred = model.predict(X_test)
            
            if cfg.problem_type == "classification":
                result.metrics["accuracy"] = float(accuracy_score(y_test, y_pred))
                
                # Check for binary vs multi-class
                unique_classes = len(set(y))
                avg_method = "binary" if unique_classes == 2 else "weighted"
                
                result.metrics["precision"] = float(precision_score(y_test, y_pred, average=avg_method, zero_division=0))
                result.metrics["recall"] = float(recall_score(y_test, y_pred, average=avg_method, zero_division=0))
                result.metrics["f1_score"] = float(f1_score(y_test, y_pred, average=avg_method, zero_division=0))
                
                if hasattr(model, "predict_proba") and unique_classes == 2:
                    y_prob = model.predict_proba(X_test)[:, 1]
                    result.metrics["roc_auc"] = float(roc_auc_score(y_test, y_prob))
                    
            elif cfg.problem_type == "regression":
                result.metrics["mse"] = float(mean_squared_error(y_test, y_pred))
                result.metrics["rmse"] = float(root_mean_squared_error(y_test, y_pred))
                result.metrics["mae"] = float(mean_absolute_error(y_test, y_pred))
                result.metrics["r2"] = float(r2_score(y_test, y_pred))
                
        elif cfg.problem_type == "clustering":
            # Unsupervised
            X = df
            model = ModelFactory.create_model(cfg.problem_type, cfg.algorithm, cfg.parameters)
            
            if cfg.algorithm == "dbscan":
                labels = model.fit_predict(X)
            else:
                model.fit(X)
                labels = model.labels_
                
            result.model = model
            
            # Evaluate only if we have more than 1 cluster and less than n_samples
            if len(set(labels)) > 1 and len(set(labels)) < len(X):
                result.metrics["silhouette_score"] = float(silhouette_score(X, labels))
            else:
                result.metrics["silhouette_score"] = 0.0

        logger.info("training_completed", dataset=dataset_name, metrics=result.metrics)
        
    except Exception as exc:
        logger.error("training_failed", error=str(exc))
        result.errors.append(str(exc))
        raise

    return result
