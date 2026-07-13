"""
Feature Scaler
==============
Standard / MinMax / Robust / MaxAbs / Normalizer.
In 'auto' mode: use RobustScaler (handles outliers well — production default).
Scaler is fitted and stored in metadata for pipeline reuse.
"""
from __future__ import annotations
from typing import Any
import pandas as pd
import numpy as np
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler,
    MaxAbsScaler, Normalizer
)
from app.services.preprocessing.config import ScalingConfig

_SCALERS = {
    "standard":   StandardScaler,
    "minmax":     MinMaxScaler,
    "robust":     RobustScaler,
    "maxabs":     MaxAbsScaler,
    "normalizer": Normalizer,
}


def scale_features(
    df: pd.DataFrame,
    cfg: ScalingConfig,
    exclude_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = df.copy()
    exclude = set(exclude_columns or [])
    numeric_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns
        if c not in exclude
    ]

    strategy = cfg.strategy if cfg.strategy != "auto" else "robust"

    if strategy == "none" or not numeric_cols:
        return df, {"strategy": "none", "scaled_columns": []}

    ScalerClass = _SCALERS[strategy]
    scaler = ScalerClass()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])

    return df, {
        "strategy":        strategy,
        "scaled_columns":  numeric_cols,
        "scaler_params":   _get_params(scaler, strategy),
    }


def _get_params(scaler, strategy: str) -> dict:
    try:
        if strategy == "standard":
            return {"mean": list(scaler.mean_), "scale": list(scaler.scale_)}
        if strategy == "minmax":
            return {"min": list(scaler.data_min_), "max": list(scaler.data_max_)}
        if strategy == "robust":
            return {"center": list(scaler.center_), "scale": list(scaler.scale_)}
    except AttributeError:
        pass
    return {}
