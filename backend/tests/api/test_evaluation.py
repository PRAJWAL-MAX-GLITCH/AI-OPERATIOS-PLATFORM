"""
Evaluation Engine Tests
=======================
Tests for AutoML pipelines, metrics, visualizations, and API.
"""
import pytest
from pathlib import Path
import pandas as pd
import uuid

from app.services.evaluation.config import AutoMLConfig, CVConfig
from app.services.evaluation.automl_pipeline import run_automl_pipeline
from app.services.evaluation.metrics import (
    compute_classification_metrics,
    compute_regression_metrics,
    compute_clustering_metrics
)

ADULT_PATH = Path(r"C:\Users\prajw\Downloads\adult\adult.data")
ADULT_COLS = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country", "income"
]

@pytest.fixture(scope="module")
def adult_df():
    df = pd.read_csv(
        ADULT_PATH, header=None, names=ADULT_COLS,
        na_values=["?", "", " "], skipinitialspace=True,
    )
    df = df.dropna().head(2000) # subset for faster cv
    # Basic encoding for test
    for col in df.select_dtypes(include=["object"]):
        df[col] = df[col].astype("category").cat.codes
    return df


def test_classification_metrics():
    y_true = [0, 1, 0, 1, 0, 0, 1, 1]
    y_pred = [0, 1, 0, 0, 0, 1, 1, 1]
    y_prob = [0.1, 0.9, 0.2, 0.4, 0.3, 0.6, 0.8, 0.9]
    
    metrics = compute_classification_metrics(y_true, y_pred, y_prob)
    assert "accuracy" in metrics
    assert "specificity" in metrics
    assert "roc_auc" in metrics
    assert "pr_auc" in metrics


def test_regression_metrics():
    y_true = [1.0, 2.0, 3.0, 4.0]
    y_pred = [1.1, 1.9, 3.2, 3.8]
    metrics = compute_regression_metrics(y_true, y_pred)
    assert "rmse" in metrics
    assert "mape" in metrics
    assert "r2" in metrics


def test_clustering_metrics(adult_df):
    from sklearn.cluster import KMeans
    X = adult_df.drop(columns=["income"]).head(100)
    model = KMeans(n_clusters=2, n_init=2)
    labels = model.fit_predict(X)
    
    metrics = compute_clustering_metrics(X, labels)
    assert "silhouette_score" in metrics
    assert "davies_bouldin" in metrics


def test_automl_classification(adult_df):
    cfg = AutoMLConfig(
        problem_type="classification",
        target_column="income",
        primary_metric="f1_score",
        algorithms=["logistic_regression", "decision_tree"],
        cv=CVConfig(folds=2)
    )
    result = run_automl_pipeline(adult_df, cfg, "adult")
    
    assert "leaderboard" in result
    assert "best_algorithm" in result
    assert "report" in result
    assert len(result["leaderboard"]) == 2
    
    # Leaderboard should be sorted by f1_score descending
    lb = result["leaderboard"]
    assert lb[0]["metrics"]["f1_score"] >= lb[1]["metrics"]["f1_score"]
    assert lb[0]["rank"] == 1
    
    # Check visuals were generated
    visuals = result["report"]["visualizations"]
    assert "confusion_matrix" in visuals
    assert "roc_curve" in visuals


def test_automl_regression(adult_df):
    cfg = AutoMLConfig(
        problem_type="regression",
        target_column="age",
        primary_metric="rmse",
        algorithms=["linear_regression", "ridge"],
        cv=CVConfig(folds=2)
    )
    result = run_automl_pipeline(adult_df, cfg, "adult")
    
    # RMSE should be sorted ascending
    lb = result["leaderboard"]
    assert lb[0]["metrics"]["rmse"] <= lb[1]["metrics"]["rmse"]
    assert lb[0]["rank"] == 1


# API Boundaries
def test_evaluation_start_auth(client):
    res = client.post(
        f"/api/v1/projects/{uuid.uuid4()}/datasets/{uuid.uuid4()}/evaluation/start",
        json={"problem_type": "classification", "cv_folds": 3}
    )
    assert res.status_code == 401


def test_evaluation_leaderboard_auth(client):
    res = client.get(
        f"/api/v1/projects/{uuid.uuid4()}/datasets/{uuid.uuid4()}/models/leaderboard"
    )
    assert res.status_code == 401
