"""
DL Inference Engine
====================
Loads trained checkpoints and runs single/batch inference.
"""
from __future__ import annotations
import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any
import structlog

from app.services.deep_learning.models import DLModelFactory
from app.services.deep_learning.config import get_device

logger = structlog.get_logger(__name__)


class DLInferenceEngine:

    @staticmethod
    def load_model_from_checkpoint(
        checkpoint_path: str,
        problem_type: str,
        input_dim: int,
        model_config: dict[str, Any],
    ) -> tuple[nn.Module, torch.device]:
        """Reconstruct and load a trained model from checkpoint."""
        device = get_device()
        model  = DLModelFactory.create(problem_type, input_dim, model_config)
        state  = torch.load(checkpoint_path, map_location=device, weights_only=True)
        model.load_state_dict(state)
        model.eval()
        model.to(device)
        logger.info("dl_model_loaded", path=checkpoint_path, device=str(device))
        return model, device

    @staticmethod
    def predict(
        model: nn.Module,
        device: torch.device,
        X: np.ndarray,
        problem_type: str,
    ) -> dict[str, Any]:
        """
        Runs inference on an array of features.
        Returns prediction and probability/confidence.
        """
        tensor = torch.tensor(X, dtype=torch.float32).to(device)
        with torch.no_grad():
            logits = model(tensor)

        if problem_type == "binary_classification":
            probs = torch.sigmoid(logits).cpu().numpy()
            preds = (probs >= 0.5).astype(int)
            return {
                "predictions": preds.tolist(),
                "probabilities": probs.tolist(),
                "confidence": probs.tolist(),
            }
        elif problem_type == "multiclass_classification":
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            preds = probs.argmax(axis=-1)
            return {
                "predictions": preds.tolist(),
                "probabilities": probs.tolist(),
                "confidence": probs.max(axis=-1).tolist(),
            }
        else:  # regression
            vals = logits.cpu().numpy()
            return {
                "predictions": vals.tolist(),
                "probabilities": None,
                "confidence": None,
            }


dl_inference = DLInferenceEngine()
