"""
AutoML Pipeline Orchestrator
=============================
Evaluates multiple algorithms via CV, runs optional HPO, and builds a leaderboard.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
import time
import structlog
from typing import Any
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_predict

from app.services.evaluation.config import AutoMLConfig
from app.services.evaluation.metrics import (
    compute_classification_metrics,
    compute_regression_metrics,
    compute_clustering_metrics
)
from app.services.evaluation.visualizer import plot_confusion_matrix, plot_roc_curve, plot_residuals
from app.services.training.factory import ModelFactory
from app.services.training.serializer import save_model

logger = structlog.get_logger(__name__)


def _get_default_algorithms(problem_type: str) -> list[str]:
    if problem_type == "classification":
        return ["logistic_regression", "random_forest", "decision_tree"]
    elif problem_type == "regression":
        return ["linear_regression", "random_forest", "ridge"]
    elif problem_type == "clustering":
        return ["kmeans"]
    return []


def run_automl_pipeline(
    df: pd.DataFrame,
    cfg: AutoMLConfig,
    dataset_name: str = "dataset"
) -> dict[str, Any]:
    
    logger.info("automl_started", dataset=dataset_name, problem_type=cfg.problem_type)
    
    algorithms = cfg.algorithms or _get_default_algorithms(cfg.problem_type)
    
    X = df.drop(columns=[cfg.target_column]) if cfg.target_column else df
    y = df[cfg.target_column] if cfg.target_column else None
    
    if cfg.problem_type == "classification":
        cv = StratifiedKFold(n_splits=cfg.cv.folds, shuffle=True, random_state=cfg.cv.random_state)
    else:
        cv = KFold(n_splits=cfg.cv.folds, shuffle=True, random_state=cfg.cv.random_state)
    
    leaderboard = []
    
    # Evaluate each algorithm
    for algo in algorithms:
        try:
            start_time = time.time()
            model = ModelFactory.create_model(cfg.problem_type, algo, {})
            
            if cfg.problem_type in ["classification", "regression"]:
                # We use cross_val_predict for Out-Of-Fold predictions to calculate metrics on the whole set
                # For classification, we also want probabilities if available
                y_pred = cross_val_predict(model, X, y, cv=cv, method="predict")
                
                y_prob = None
                if cfg.problem_type == "classification" and hasattr(model, "predict_proba"):
                    y_prob = cross_val_predict(model, X, y, cv=cv, method="predict_proba")
                    if len(set(y)) == 2:
                        y_prob = y_prob[:, 1]
                
                # Fit a final model on all data for the final artifact
                model.fit(X, y)
                
                if cfg.problem_type == "classification":
                    metrics = compute_classification_metrics(y, y_pred, y_prob)
                else:
                    metrics = compute_regression_metrics(y, y_pred)
                    
            elif cfg.problem_type == "clustering":
                labels = model.fit_predict(X)
                metrics = compute_clustering_metrics(X, labels)
                y_pred = labels
                
            end_time = time.time()
            
            leaderboard.append({
                "algorithm": algo,
                "metrics": metrics,
                "training_time_seconds": round(end_time - start_time, 2),
                "model_instance": model,
                "y_pred": y_pred,
                "y_prob": y_prob if 'y_prob' in locals() else None,
            })
            
        except Exception as exc:
            logger.error("automl_algo_failed", algo=algo, error=str(exc))
            
    if not leaderboard:
        raise RuntimeError("No algorithms succeeded in training.")
        
    # Rank algorithms
    # Determine sort direction based on metric (higher is better for f1/r2/accuracy, lower for mse/rmse)
    primary_metric = cfg.primary_metric
    if not primary_metric:
        if cfg.problem_type == "classification":
            primary_metric = "f1_score"
        elif cfg.problem_type == "regression":
            primary_metric = "r2"
        else:
            primary_metric = "silhouette_score"

    reverse_sort = primary_metric not in ["mse", "rmse", "mae", "mape", "median_ae", "davies_bouldin"]
    
    # Sort leaderboard
    leaderboard.sort(key=lambda x: x["metrics"].get(primary_metric, 0), reverse=reverse_sort)
    
    for i, entry in enumerate(leaderboard):
        entry["rank"] = i + 1

    best_entry = leaderboard[0]
    
    # Generate Visualizations for Best Model
    visualizations = {}
    if cfg.problem_type == "classification" and y is not None:
        visualizations["confusion_matrix"] = plot_confusion_matrix(y, best_entry["y_pred"])
        if best_entry["y_prob"] is not None and len(set(y)) == 2:
            visualizations["roc_curve"] = plot_roc_curve(y, best_entry["y_prob"])
    elif cfg.problem_type == "regression" and y is not None:
        visualizations["residual_plot"] = plot_residuals(y, best_entry["y_pred"])
        
    report = {
        "best_algorithm": best_entry["algorithm"],
        "primary_metric": primary_metric,
        "best_score": best_entry["metrics"].get(primary_metric, 0),
        "visualizations": visualizations,
        "recommendation": f"Model {best_entry['algorithm']} selected based on {primary_metric}.",
        "strengths": "Fast inference" if best_entry["training_time_seconds"] < 5 else "High capacity",
    }
    
    # Remove large non-serializable objects from leaderboard dicts before returning
    best_model_instance = best_entry["model_instance"]
    
    for entry in leaderboard:
        entry.pop("model_instance", None)
        # Convert arrays to list for JSON serialization
        if isinstance(entry.get("y_pred"), np.ndarray):
            entry.pop("y_pred", None)
        if isinstance(entry.get("y_prob"), np.ndarray):
            entry.pop("y_prob", None)
            
    return {
        "leaderboard": leaderboard,
        "report": report,
        "best_model_instance": best_model_instance,
        "best_algorithm": best_entry["algorithm"],
        "best_metrics": best_entry["metrics"]
    }
