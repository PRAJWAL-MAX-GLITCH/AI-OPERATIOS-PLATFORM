"""
Outlier Detector
================
Implements IQR and Z-Score outlier detection.
Also provides a placeholder for Isolation Forest.
Does NOT remove outliers — only detects and counts them.

Enterprise rule: outlier removal decisions belong to the Data Scientist,
not the platform. We only surface the information.
"""
from __future__ import annotations
from typing import Any
import pandas as pd
import numpy as np


Z_SCORE_THRESHOLD = 3.0


def detect_outliers(df: pd.DataFrame) -> dict[str, Any]:
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    per_column: dict[str, Any] = {}
    warnings: list[str] = []

    for col in numeric_cols:
        s = df[col].dropna()
        if len(s) < 10:
            continue

        iqr_result  = _iqr_outliers(s)
        zscore_result = _zscore_outliers(s)

        per_column[col] = {
            "iqr":     iqr_result,
            "z_score": zscore_result,
            "isolation_forest": {
                "status": "placeholder",
                "note":   "Enable by installing scikit-learn and calling IsolationForest",
            },
        }

        total_outliers = iqr_result["outlier_count"]
        if total_outliers > 0:
            pct = round(total_outliers / len(df) * 100, 2)
            warnings.append(
                f"Column '{col}': {total_outliers} IQR outliers ({pct}%)"
            )

    return {
        "numeric_columns_checked": len(numeric_cols),
        "per_column":  per_column,
        "warnings":    warnings,
    }


def _iqr_outliers(s: pd.Series) -> dict[str, Any]:
    q1 = float(s.quantile(0.25))
    q3 = float(s.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    mask = (s < lower) | (s > upper)
    return {
        "q1":            round(q1, 4),
        "q3":            round(q3, 4),
        "iqr":           round(iqr, 4),
        "lower_fence":   round(lower, 4),
        "upper_fence":   round(upper, 4),
        "outlier_count": int(mask.sum()),
        "outlier_pct":   round(mask.mean() * 100, 2),
    }


def _zscore_outliers(s: pd.Series) -> dict[str, Any]:
    mean = float(s.mean())
    std  = float(s.std())
    if std == 0:
        return {"outlier_count": 0, "outlier_pct": 0.0, "threshold": Z_SCORE_THRESHOLD}
    z = ((s - mean) / std).abs()
    mask = z > Z_SCORE_THRESHOLD
    return {
        "threshold":     Z_SCORE_THRESHOLD,
        "outlier_count": int(mask.sum()),
        "outlier_pct":   round(mask.mean() * 100, 2),
    }
