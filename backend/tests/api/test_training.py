"""
Training API Tests
==================
Tests for the Training Engine endpoints and pipeline logic.
"""
import pytest
from pathlib import Path
import pandas as pd
import uuid

from app.services.training.config import TrainingConfig, SplitConfig
from app.services.training.pipeline import run_training_pipeline
from app.services.training.serializer import save_model, load_model

ADULT_PATH = Path(r"C:\Users\prajw\Downloads\adult\adult.data")
TELCO_PATH = Path(r"C:\Users\prajw\Downloads\archive (1)\Telco_customer_churn.xlsx")
ADULT_COLS = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country", "income"
]

@pytest.fixture(scope="module")
def adult_df():
    # Load and do very basic preprocessing just so models can train
    # Real pipeline uses preprocessing engine, but we mock it for pipeline logic tests
    df = pd.read_csv(
        ADULT_PATH, header=None, names=ADULT_COLS,
        na_values=["?", "", " "], skipinitialspace=True,
    )
    df = df.dropna()
    # Basic encoding for test
    for col in df.select_dtypes(include=["object"]):
        df[col] = df[col].astype("category").cat.codes
    return df


def test_classification_pipeline(adult_df):
    cfg = TrainingConfig(
        problem_type="classification",
        target_column="income",
        algorithm="logistic_regression",
        parameters={"max_iter": 100}
    )
    result = run_training_pipeline(adult_df, cfg, "adult")
    
    assert result.algorithm == "logistic_regression"
    assert result.problem_type == "classification"
    assert "accuracy" in result.metrics
    assert "f1_score" in result.metrics
    assert result.model is not None


def test_regression_pipeline(adult_df):
    # Predict age instead of income
    cfg = TrainingConfig(
        problem_type="regression",
        target_column="age",
        algorithm="linear_regression",
    )
    result = run_training_pipeline(adult_df, cfg, "adult")
    
    assert result.algorithm == "linear_regression"
    assert result.problem_type == "regression"
    assert "mse" in result.metrics
    assert "r2" in result.metrics
    assert result.model is not None


def test_clustering_pipeline(adult_df):
    # Clustering on subset
    df_sample = adult_df.head(1000)
    cfg = TrainingConfig(
        problem_type="clustering",
        algorithm="kmeans",
        parameters={"n_clusters": 3, "n_init": "auto"}
    )
    result = run_training_pipeline(df_sample, cfg, "adult_sample")
    
    assert result.algorithm == "kmeans"
    assert result.problem_type == "clustering"
    assert "silhouette_score" in result.metrics
    assert result.model is not None


def test_model_serialization(adult_df):
    cfg = TrainingConfig(
        problem_type="classification",
        target_column="income",
        algorithm="decision_tree",
    )
    result = run_training_pipeline(adult_df, cfg, "adult")
    
    dataset_id = str(uuid.uuid4())
    project_id = str(uuid.uuid4())
    meta = {"algorithm": "decision_tree"}
    
    path = save_model(result.model, dataset_id, project_id, meta)
    
    loaded_model, loaded_meta = load_model(path)
    assert loaded_meta["dataset_id"] == dataset_id
    assert loaded_meta["algorithm"] == "decision_tree"
    
    # Check model still works
    X = adult_df.drop(columns=["income"])
    preds = loaded_model.predict(X.head(5))
    assert len(preds) == 5


def test_unsupported_algorithm():
    cfg = TrainingConfig(
        problem_type="classification",
        target_column="income",
        algorithm="linear_regression",  # Linear regression is for regression, not classification
    )
    
    # We can use empty df here because factory throws error before fitting
    df = pd.DataFrame({"income": [0,1], "feat": [1,2]})
    with pytest.raises(Exception, match="not supported for classification"):
        run_training_pipeline(df, cfg, "test")


# API Auth boundaries
def test_training_start_endpoint_requires_auth(client):
    pid = str(uuid.uuid4())
    did = str(uuid.uuid4())
    res = client.post(
        f"/api/v1/projects/{pid}/datasets/{did}/training/start",
        json={"problem_type": "classification", "algorithm": "random_forest"}
    )
    assert res.status_code == 401


def test_training_jobs_endpoint_requires_auth(client):
    pid = str(uuid.uuid4())
    did = str(uuid.uuid4())
    res = client.get(f"/api/v1/projects/{pid}/datasets/{did}/training/jobs")
    assert res.status_code == 401
