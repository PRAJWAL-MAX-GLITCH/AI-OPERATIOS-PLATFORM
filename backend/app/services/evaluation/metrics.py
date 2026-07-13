"""
Metrics Engine
==============
Calculates extended enterprise metrics for model evaluation.
"""
from __future__ import annotations
import numpy as np
from typing import Any
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    balanced_accuracy_score, matthews_corrcoef, cohen_kappa_score,
    mean_squared_error, root_mean_squared_error, mean_absolute_error, r2_score,
    mean_absolute_percentage_error, median_absolute_error, explained_variance_score,
    silhouette_score, davies_bouldin_score, calinski_harabasz_score,
    average_precision_score
)


def compute_classification_metrics(y_true, y_pred, y_prob=None) -> dict[str, float]:
    unique_classes = len(set(y_true))
    is_binary = unique_classes == 2
    avg_method = "binary" if is_binary else "weighted"
    
    metrics = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, average=avg_method, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, average=avg_method, zero_division=0)),
        "f1_score": float(f1_score(y_true, y_pred, average=avg_method, zero_division=0)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)),
        "kappa": float(cohen_kappa_score(y_true, y_pred)),
    }
    
    if y_prob is not None:
        try:
            if is_binary:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob))
                metrics["pr_auc"] = float(average_precision_score(y_true, y_prob))
            else:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_prob, multi_class="ovr"))
        except ValueError:
            pass  # in case of missing classes in fold

    # Approximate Specificity / Sensitivity if binary
    if is_binary:
        y_true_np = np.array(y_true)
        y_pred_np = np.array(y_pred)
        tn = np.sum((y_true_np == 0) & (y_pred_np == 0))
        fp = np.sum((y_true_np == 0) & (y_pred_np == 1))
        metrics["specificity"] = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        metrics["sensitivity"] = metrics["recall"]
        
    return metrics


def compute_regression_metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "mse": float(mean_squared_error(y_true, y_pred)),
        "rmse": float(root_mean_squared_error(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "mape": float(mean_absolute_percentage_error(y_true, y_pred)),
        "median_ae": float(median_absolute_error(y_true, y_pred)),
        "explained_variance": float(explained_variance_score(y_true, y_pred)),
    }


def compute_clustering_metrics(X, labels) -> dict[str, float]:
    if len(set(labels)) <= 1 or len(set(labels)) >= len(X):
        return {
            "silhouette_score": 0.0,
            "davies_bouldin": 0.0,
            "calinski_harabasz": 0.0,
        }
        
    return {
        "silhouette_score": float(silhouette_score(X, labels)),
        "davies_bouldin": float(davies_bouldin_score(X, labels)),
        "calinski_harabasz": float(calinski_harabasz_score(X, labels)),
    }
