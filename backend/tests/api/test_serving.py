import pytest
import uuid
import pandas as pd
from sklearn.linear_model import LogisticRegression

from app.services.mlops.experiment_tracker import experiment_tracker
from app.services.mlops.model_registry import model_registry
from app.services.serving.prediction_pipeline import run_prediction_pipeline


def _create_mock_mlflow_model():
    """Trains a simple dummy model and registers it to MLflow for testing."""
    # Dummy data
    df = pd.DataFrame({"age": [25, 30, 45, 50], "income": [50000, 60000, 80000, 90000]})
    y = [0, 0, 1, 1]
    
    model = LogisticRegression()
    model.fit(df, y)
    
    project_id = str(uuid.uuid4())
    dataset_id = str(uuid.uuid4())
    model_name = f"Test_Model_{project_id}"
    
    run_id = experiment_tracker.log_training_run(
        project_id=project_id,
        dataset_id=dataset_id,
        dataset_name="dummy_data",
        algorithm="logistic_regression",
        metrics={"accuracy": 1.0},
        params={},
        model=model
    )
    
    mv = model_registry.register_model(run_id, model_name)
    model_registry.transition_stage(model_name, mv.version, "Production")
    
    return model_name, str(mv.version)


def test_prediction_pipeline_basic():
    """Test online prediction pipeline without explainability."""
    model_name, version = _create_mock_mlflow_model()
    
    payload = {"age": 48, "income": 85000}
    prediction, confidence, explanation = run_prediction_pipeline(
        model_name=model_name,
        version=version,
        payload=payload,
        explain=False
    )
    
    assert prediction is not None
    assert confidence is not None
    assert explanation is None


def test_prediction_pipeline_explain():
    """Test online prediction pipeline with SHAP explainability."""
    model_name, version = _create_mock_mlflow_model()
    
    payload = {"age": 48, "income": 85000}
    prediction, confidence, explanation = run_prediction_pipeline(
        model_name=model_name,
        version=version,
        payload=payload,
        explain=True
    )
    
    assert prediction is not None
    assert confidence is not None
    assert explanation is not None
    assert "waterfall_plot_base64" in explanation
    assert "contributions" in explanation
    assert "age" in explanation["contributions"]
    assert "income" in explanation["contributions"]
