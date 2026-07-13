"""
Feature Transformer
====================
Log, Sqrt, Power (Box-Cox / Yeo-Johnson).
Auto mode: applies Yeo-Johnson to columns with |skewness| > threshold.
Yeo-Johnson handles negative values; Box-Cox requires positive values.
"""
from __future__ import annotations
from typing import Any
import warnings
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats
from app.services.preprocessing.config import TransformationConfig


def transform_features(
    df: pd.DataFrame,
    cfg: TransformationConfig,
    exclude_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = df.copy()
    exclude = set(exclude_columns or [])
    numeric_cols = [
        c for c in df.select_dtypes(include=[np.number]).columns
        if c not in exclude
    ]
    actions: dict[str, str] = {}

    for col in numeric_cols:
        s = df[col].dropna()
        skewness = float(s.skew())

        if cfg.auto_transform_skewed and abs(skewness) > cfg.skew_threshold:
            df[col], method = _yeo_johnson(df[col])
            actions[col] = f"yeo_johnson (skewness was {skewness:.2f})"
            continue

        if cfg.apply_log:
            if (df[col] > 0).all():
                df[col] = np.log1p(df[col])
                actions[col] = "log1p"
        elif cfg.apply_sqrt:
            if (df[col] >= 0).all():
                df[col] = np.sqrt(df[col])
                actions[col] = "sqrt"
        elif cfg.apply_yeo_johnson:
            df[col], method = _yeo_johnson(df[col])
            actions[col] = f"yeo_johnson"

    return df, {"transformed_columns": actions}


def _yeo_johnson(series: pd.Series) -> tuple[pd.Series, str]:
    """Apply Yeo-Johnson power transform (handles negatives, zeros)."""
    arr = series.to_numpy(dtype=float, na_value=np.nan)
    non_null = ~np.isnan(arr)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        transformed, lmbda = scipy_stats.yeojohnson(arr[non_null])
    arr[non_null] = transformed
    return pd.Series(arr, index=series.index, name=series.name), f"yeo_johnson(λ={lmbda:.4f})"
