"""
Enterprise Dataset Profiler
Generates statistical profiles mimicking Databricks / Dataiku data profiling:
- Numeric column summaries (mean, std, min, max, quartiles)
- Categorical column summaries (top values, frequency)
- Missing value heatmap
- Memory usage report
"""
import pandas as pd
from typing import Any
import structlog

logger = structlog.get_logger(__name__)


def generate_profile(df: pd.DataFrame, dataset_name: str = "") -> dict[str, Any]:
    """
    Run full data profiling on a DataFrame.
    Returns a JSON-serialisable profile dict.
    """
    logger.info("profiling_started", dataset=dataset_name, rows=len(df), cols=len(df.columns))

    total_rows = len(df)
    total_cells = df.size
    missing_cells = int(df.isna().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    column_profiles: dict[str, Any] = {}

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        unique_count = int(series.nunique(dropna=True))

        col_info: dict[str, Any] = {
            "dtype": str(series.dtype),
            "null_count": null_count,
            "null_pct": round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0,
            "unique_count": unique_count,
        }

        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            col_info["type"] = "numeric"
            col_info["stats"] = {
                "mean": _safe_float(desc.get("mean")),
                "std": _safe_float(desc.get("std")),
                "min": _safe_float(desc.get("min")),
                "25pct": _safe_float(desc.get("25%")),
                "50pct": _safe_float(desc.get("50%")),
                "75pct": _safe_float(desc.get("75%")),
                "max": _safe_float(desc.get("max")),
            }
        elif pd.api.types.is_datetime64_any_dtype(series):
            col_info["type"] = "datetime"
            col_info["stats"] = {
                "min": str(series.min()),
                "max": str(series.max()),
            }
        else:
            col_info["type"] = "categorical"
            top_values = series.value_counts(dropna=True).head(10).to_dict()
            col_info["top_values"] = {str(k): int(v) for k, v in top_values.items()}

        column_profiles[col] = col_info

    profile = {
        "summary": {
            "total_rows": total_rows,
            "total_columns": len(df.columns),
            "total_cells": total_cells,
            "missing_cells": missing_cells,
            "missing_pct": round((missing_cells / total_cells) * 100, 2) if total_cells > 0 else 0,
            "duplicate_rows": duplicate_rows,
            "duplicate_pct": round((duplicate_rows / total_rows) * 100, 2) if total_rows > 0 else 0,
            "memory_usage_bytes": int(df.memory_usage(deep=True).sum()),
        },
        "columns": column_profiles,
    }

    logger.info("profiling_complete", dataset=dataset_name, missing_pct=profile["summary"]["missing_pct"])
    return profile


def _safe_float(val: Any) -> float | None:
    """Safely convert numpy floats to Python floats for JSON serialization."""
    try:
        return round(float(val), 6)
    except (TypeError, ValueError):
        return None
