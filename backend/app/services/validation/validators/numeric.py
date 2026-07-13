"""
Numeric Analyser
================
Computes descriptive statistics for all numeric columns.
Includes skewness, kurtosis, quantiles, and variance.
"""
from __future__ import annotations
from typing import Any
import pandas as pd
import numpy as np


def analyse_numeric(df: pd.DataFrame) -> dict[str, Any]:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    per_column: dict[str, Any] = {}

    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) == 0:
            continue
        per_column[col] = {
            "count":    int(s.count()),
            "mean":     _f(s.mean()),
            "median":   _f(s.median()),
            "mode":     _f(s.mode().iloc[0]) if not s.mode().empty else None,
            "std":      _f(s.std()),
            "variance": _f(s.var()),
            "min":      _f(s.min()),
            "max":      _f(s.max()),
            "skewness": _f(s.skew()),
            "kurtosis": _f(s.kurtosis()),
            "q1":       _f(s.quantile(0.25)),
            "q3":       _f(s.quantile(0.75)),
            "iqr":      _f(s.quantile(0.75) - s.quantile(0.25)),
            "p5":       _f(s.quantile(0.05)),
            "p95":      _f(s.quantile(0.95)),
        }

    warnings: list[str] = []
    for col, stats in per_column.items():
        skew = stats.get("skewness") or 0
        if abs(skew) > 2:
            warnings.append(f"Column '{col}' is highly skewed (skewness={skew:.2f})")

    return {
        "numeric_column_count": len(numeric_cols),
        "numeric_columns":      numeric_cols,
        "per_column":           per_column,
        "warnings":             warnings,
    }


def _f(val: Any) -> float | None:
    try:
        return round(float(val), 6)
    except (TypeError, ValueError):
        return None
