"""
MLOps Testing
=============
Verifies mlflow experiment tracking and model registry operations.
"""
import pytest
import uuid
from sklearn.linear_model import LogisticRegression

from app.services.mlops.experiment_tracker import experiment_tracker
from app.services.mlops.model_registry import model_registry


def test_experiment_tracking():
    # Simulate tracking a model
    model = LogisticRegression()
    
    run_id = experiment_tracker.log_training_run(
        project_id=str(uuid.uuid4()),
        dataset_id=str(uuid.uuid4()),
        dataset_name="test_dataset",
        algorithm="logistic_regression",
        metrics={"accuracy": 0.95},
        params={"C": 1.0},
        model=model,
        run_name="Test Run"
    )
    
    assert run_id is not None
    assert isinstance(run_id, str)
    return run_id


def test_model_registry():
    # Generate a run first
    run_id = test_experiment_tracking()
    model_name = f"Test_Model_{uuid.uuid4()}"
    
    # 1. Register the model
    mv = model_registry.register_model(run_id, model_name)
    assert str(mv.version) == "1"
    
    # 2. List versions
    versions = model_registry.get_latest_versions(model_name)
    assert len(versions) >= 1
    assert versions[0]["name"] == model_name
    
    # 3. Transition to Staging
    model_registry.transition_stage(model_name, mv.version, "Staging")
    
    # 4. Verify Transition
    versions_staging = model_registry.get_latest_versions(model_name, stages=["Staging"])
    assert len(versions_staging) == 1
    assert versions_staging[0]["current_stage"] == "Staging"
    

def test_api_list_models_auth(client):
    res = client.get("/api/v1/mlops/models")
    assert res.status_code == 401


def test_api_transition_stage_auth(client):
    res = client.post(
        "/api/v1/mlops/models/Some_Model/stage",
        json={"version": "1", "stage": "Production"}
    )
    assert res.status_code == 401
