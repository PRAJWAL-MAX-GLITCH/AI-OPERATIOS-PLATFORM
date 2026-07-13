"""
Categorical Analyser
====================
Computes cardinality, frequency distributions, and flags rare categories
for all categorical / string / boolean columns.
"""
from __future__ import annotations
from typing import Any
import pandas as pd


# If a category appears in < 1% of rows it is considered "rare"
RARE_THRESHOLD = 0.01


def analyse_categorical(df: pd.DataFrame) -> dict[str, Any]:
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    per_column: dict[str, Any] = {}
    warnings: list[str] = []
    total_rows = len(df)

    for col in cat_cols:
        s = df[col].dropna()
        vc = s.value_counts(dropna=True)
        n_unique = int(s.nunique())
        cardinality_ratio = round(n_unique / total_rows, 4) if total_rows > 0 else 0

        # Rare categories: appear fewer than RARE_THRESHOLD * total_rows times
        rare_cutoff = max(1, RARE_THRESHOLD * total_rows)
        rare_cats = [str(k) for k, v in vc.items() if v < rare_cutoff]

        # Top 20 values for display
        top_values = {str(k): int(v) for k, v in vc.head(20).items()}

        per_column[col] = {
            "unique_count":      n_unique,
            "cardinality_ratio": cardinality_ratio,
            "top_values":        top_values,
            "rare_categories":   rare_cats[:20],
            "rare_count":        len(rare_cats),
        }

        if n_unique == total_rows:
            warnings.append(f"Column '{col}' has 100% unique values (possible ID column)")
        if len(rare_cats) > n_unique * 0.5:
            warnings.append(f"Column '{col}' has many rare categories ({len(rare_cats)})")

    return {
        "categorical_column_count": len(cat_cols),
        "categorical_columns":      cat_cols,
        "per_column":               per_column,
        "warnings":                 warnings,
    }
