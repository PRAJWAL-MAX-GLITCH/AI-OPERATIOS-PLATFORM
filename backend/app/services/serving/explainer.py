"""
Explainable AI Engine (SHAP)
============================
Provides local feature importance for single predictions.
"""
from __future__ import annotations
import shap
import base64
import io
import structlog
import matplotlib.pyplot as plt
import pandas as pd
from typing import Any

logger = structlog.get_logger(__name__)

# Use a non-interactive backend
plt.switch_backend("Agg")


class Explainer:

    @staticmethod
    def _get_base64_image(fig) -> str:
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    @staticmethod
    def generate_local_explanation(
        model: Any,
        features_df: pd.DataFrame,
        background_data: pd.DataFrame = None
    ) -> dict[str, Any]:
        """
        Generates SHAP values for a single prediction row.
        Returns a dict containing feature contributions and a base64 waterfall plot.
        """
        try:
            # Determine explainer type
            if hasattr(model, "predict_proba"):
                explainer = shap.Explainer(model.predict, background_data if background_data is not None else features_df)
            else:
                # Tree models or linear
                explainer = shap.Explainer(model)
                
            shap_values = explainer(features_df)
            
            # Extract contributions for the single row
            # For classification, shap_values might be 3D. We take the output for class 1 if binary.
            if len(shap_values.shape) == 3:
                values = shap_values[0, :, 1].values
                base_value = shap_values[0, :, 1].base_values
            else:
                values = shap_values[0].values
                base_value = shap_values[0].base_values

            contributions = {
                col: float(val) for col, val in zip(features_df.columns, values)
            }
            
            # Generate waterfall plot
            fig, ax = plt.subplots(figsize=(8, 5))
            if len(shap_values.shape) == 3:
                shap.plots.waterfall(shap_values[0, :, 1], show=False)
            else:
                shap.plots.waterfall(shap_values[0], show=False)
            plot_base64 = Explainer._get_base64_image(fig)

            return {
                "base_value": float(base_value),
                "contributions": contributions,
                "waterfall_plot_base64": plot_base64
            }
        except Exception as exc:
            logger.warning("shap_explanation_failed", error=str(exc))
            return {"error": str(exc)}


explainer = Explainer()
