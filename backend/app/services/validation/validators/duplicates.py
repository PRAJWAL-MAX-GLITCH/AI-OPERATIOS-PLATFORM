"""
Duplicate Detector
==================
Detects fully duplicated rows and near-identical column pairs.
"""
from __future__ import annotations
from typing import Any
import pandas as pd


def analyse_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    total_rows = len(df)

    # ── Duplicate Rows ──────────────────────────────────────── #
    dup_mask     = df.duplicated(keep="first")
    dup_count    = int(dup_mask.sum())
    dup_pct      = round(dup_count / total_rows * 100, 2) if total_rows > 0 else 0.0
    dup_row_idxs = df.index[dup_mask].tolist()[:50]  # cap to first 50 for readability

    # ── Duplicate Columns ───────────────────────────────────── #
    dup_col_pairs: list[dict[str, str]] = []
    cols = list(df.columns)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            if df[cols[i]].equals(df[cols[j]]):
                dup_col_pairs.append({"col_a": cols[i], "col_b": cols[j]})

    warnings: list[str] = []
    if dup_count > 0:
        warnings.append(f"{dup_count} duplicate rows detected ({dup_pct}%)")
    if dup_col_pairs:
        warnings.append(f"{len(dup_col_pairs)} duplicate column pair(s) detected")

    return {
        "duplicate_row_count":   dup_count,
        "duplicate_row_pct":     dup_pct,
        "duplicate_row_indices": dup_row_idxs,
        "duplicate_column_pairs": dup_col_pairs,
        "warnings":              warnings,
    }
