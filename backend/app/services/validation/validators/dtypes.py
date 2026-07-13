"""
Data Type Validator
===================
Validates each column's dtype category and flags mixed-type columns.
Provides automatic conversion suggestions.
"""
from __future__ import annotations
from typing import Any
import pandas as pd


def validate_dtypes(df: pd.DataFrame) -> dict[str, Any]:
    per_column: dict[str, Any] = {}
    mixed_cols: list[str] = []
    warnings: list[str] = []

    for col in df.columns:
        series = df[col].dropna()
        raw_dtype = str(df[col].dtype)

        if pd.api.types.is_integer_dtype(df[col]):
            category = "integer"
        elif pd.api.types.is_float_dtype(df[col]):
            category = "float"
        elif pd.api.types.is_bool_dtype(df[col]):
            category = "boolean"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            category = "datetime"
        elif raw_dtype == "object":
            # Check for mixed types inside object columns
            detected_types = set(type(v).__name__ for v in series)
            if len(detected_types) > 1:
                category = "mixed"
                mixed_cols.append(col)
            else:
                category = "string"
        elif raw_dtype == "category":
            category = "category"
        else:
            category = "unknown"

        per_column[col] = {
            "raw_dtype":    raw_dtype,
            "category":     category,
            "suggestion":   _suggest_conversion(df[col], category),
        }

    if mixed_cols:
        warnings.append(f"Mixed-type columns detected: {mixed_cols}")

    return {
        "per_column":   per_column,
        "mixed_columns": mixed_cols,
        "type_summary": _type_summary(per_column),
        "warnings":     warnings,
    }


def _suggest_conversion(series: pd.Series, category: str) -> str | None:
    import warnings
    if category != "string":
        return None
    sample = series.dropna().head(200)
    # Try numeric parse
    try:
        pd.to_numeric(sample)
        return "convert_to_numeric"
    except (ValueError, TypeError):
        pass
    # Try datetime parse — suppress pandas' UserWarning for non-date strings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            pd.to_datetime(sample, errors="raise")
        return "convert_to_datetime"
    except (ValueError, TypeError, Exception):
        pass
    # Check if low-cardinality → category
    if series.nunique() / max(len(series), 1) < 0.05:
        return "convert_to_category"
    return None


def _type_summary(per_column: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for meta in per_column.values():
        c = meta["category"]
        counts[c] = counts.get(c, 0) + 1
    return counts
