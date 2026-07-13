"""
Schema Validator
================
Validates column existence, required vs optional columns,
data type consistency, and unexpected columns.
Supports automatic schema inference when no expected schema is provided.
"""
from __future__ import annotations
from typing import Any
import pandas as pd


def validate_schema(
    df: pd.DataFrame,
    expected_schema: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Compare df columns against an expected schema dict {col_name: dtype_str}.
    When expected_schema is None, auto-infer schema from the DataFrame.
    """
    inferred: dict[str, str] = {col: str(df[col].dtype) for col in df.columns}

    if expected_schema is None:
        return {
            "status": "inferred",
            "inferred_schema": inferred,
            "total_columns": len(df.columns),
            "column_list": list(df.columns),
            "warnings": [],
        }

    expected_cols = set(expected_schema.keys())
    actual_cols   = set(df.columns)

    missing_cols     = sorted(expected_cols - actual_cols)
    unexpected_cols  = sorted(actual_cols - expected_cols)
    matching_cols    = sorted(expected_cols & actual_cols)

    type_mismatches: list[dict[str, str]] = []
    for col in matching_cols:
        expected_type = expected_schema[col].lower()
        actual_type   = str(df[col].dtype).lower()
        # Flexible matching: "int64" matches "int", "object" matches "str"
        if not _types_compatible(expected_type, actual_type):
            type_mismatches.append({
                "column":        col,
                "expected_type": expected_type,
                "actual_type":   actual_type,
            })

    warnings: list[str] = []
    if missing_cols:
        warnings.append(f"Missing expected columns: {missing_cols}")
    if unexpected_cols:
        warnings.append(f"Unexpected columns found: {unexpected_cols}")
    if type_mismatches:
        warnings.append(f"{len(type_mismatches)} column(s) have type mismatches")

    status = "passed" if not (missing_cols or type_mismatches) else "failed"

    return {
        "status":           status,
        "inferred_schema":  inferred,
        "expected_schema":  expected_schema,
        "missing_columns":  missing_cols,
        "unexpected_columns": unexpected_cols,
        "type_mismatches":  type_mismatches,
        "total_columns":    len(df.columns),
        "column_list":      list(df.columns),
        "warnings":         warnings,
    }


def _types_compatible(expected: str, actual: str) -> bool:
    """Flexible type compatibility check."""
    int_types  = {"int", "int32", "int64", "uint8", "uint16", "uint32", "uint64"}
    float_types = {"float", "float32", "float64"}
    str_types  = {"str", "object", "string", "category"}
    bool_types = {"bool", "boolean"}
    date_types = {"datetime", "datetime64", "datetime64[ns]", "datetime64[ns, utc]"}

    for group in [int_types, float_types, str_types, bool_types, date_types]:
        if expected in group and actual in group:
            return True
    return expected == actual
