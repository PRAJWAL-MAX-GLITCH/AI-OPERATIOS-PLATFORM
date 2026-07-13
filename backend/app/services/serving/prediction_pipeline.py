"""
Prediction Pipeline
===================
Orchestrates preprocessing payload -> predicting -> explaining.
"""
from __future__ import annotations
import pandas as pd
import structlog
from typing import Any, Tuple

from app.services.serving.model_loader import model_loader
from app.services.serving.explainer import explainer

logger = structlog.get_logger(__name__)


def run_prediction_pipeline(
    model_name: str,
    version: str,
    payload: dict[str, Any],
    explain: bool = False
) -> Tuple[Any, float, dict[str, Any]]:
    """
    Runs the inference pipeline.
    Returns: (prediction_result, confidence, explanation_dict)
    """
    # 1. Convert payload to DataFrame
    df = pd.DataFrame([payload])
    
    # 2. Load Model
    model = model_loader.load_model(model_name, version)
    
    # NOTE: In a true production environment, the preprocessing steps
    # should be encapsulated inside the MLflow model itself (e.g. Scikit-Learn Pipeline)
    # Since our training engine uses ModelFactory for the raw algorithm,
    # we assume the MLflow model artifact encompasses the entire `sklearn.pipeline.Pipeline`
    # or that the user sends pre-processed features for this MVP.
    
    # 3. Predict
    prediction = model.predict(df)[0]
    
    # 4. Confidence
    confidence = None
    if hasattr(model, "predict_proba"):
        try:
            probs = model.predict_proba(df)[0]
            confidence = float(max(probs))
        except Exception:
            pass
            
    # 5. Explain
    explanation = None
    if explain:
        explanation = explainer.generate_local_explanation(model, df)
        
    return prediction, confidence, explanation
