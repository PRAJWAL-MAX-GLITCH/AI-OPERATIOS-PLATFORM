"""
Missing Value Analyser
======================
Computes per-column and aggregate missing-value statistics.
Produces heatmap-ready data and imputation suggestions.
"""
from __future__ import annotations
from typing import Any
import pandas as pd


def analyse_missing(df: pd.DataFrame) -> dict[str, Any]:
    total_rows  = len(df)
    total_cells = df.size

    per_column: dict[str, Any] = {}
    for col in df.columns:
        count = int(df[col].isna().sum())
        pct   = round(count / total_rows * 100, 2) if total_rows > 0 else 0.0
        per_column[col] = {
            "missing_count": count,
            "missing_pct":   pct,
            "suggestion":    _suggest_imputation(df[col], pct),
        }

    total_missing = int(df.isna().sum().sum())
    missing_pct   = round(total_missing / total_cells * 100, 2) if total_cells > 0 else 0.0

    # Columns ranked by missingness (worst first)
    ranked = sorted(per_column.items(), key=lambda x: x[1]["missing_count"], reverse=True)

    warnings: list[str] = []
    high_missing = [c for c, v in per_column.items() if v["missing_pct"] > 30]
    if high_missing:
        warnings.append(f"Columns with >30% missing values: {high_missing}")

    return {
        "total_missing_cells": total_missing,
        "total_missing_pct":   missing_pct,
        "columns_with_missing": sum(1 for v in per_column.values() if v["missing_count"] > 0),
        "per_column":          per_column,
        "ranked_columns":      [{"column": c, **v} for c, v in ranked if v["missing_count"] > 0],
        "warnings":            warnings,
    }


def _suggest_imputation(series: pd.Series, missing_pct: float) -> str:
    if missing_pct == 0:
        return "none"
    if missing_pct > 50:
        return "consider_dropping_column"
    if pd.api.types.is_numeric_dtype(series):
        return "mean_or_median_imputation"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "forward_fill_or_interpolation"
    return "mode_or_constant_imputation"
