"""
Missing Value Handler
=====================
Supports 8 strategies. In 'auto' mode, selects strategy per column:
  numeric   → median imputation (robust to outliers)
  categorical → mode imputation
  high-missing (>50%) → drop column
"""
from __future__ import annotations
from typing import Any
import pandas as pd
from app.services.preprocessing.config import MissingConfig


def handle_missing(df: pd.DataFrame, cfg: MissingConfig) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Returns (transformed_df, step_metadata)."""
    df = df.copy()
    actions: dict[str, str] = {}
    dropped_columns: list[str] = []
    dropped_rows_count = 0

    for col in df.columns:
        missing_count = df[col].isna().sum()
        if missing_count == 0:
            actions[col] = "no_action"
            continue

        missing_pct = missing_count / len(df)
        strategy = _resolve_strategy(df[col], missing_pct, cfg)

        if strategy == "drop_columns" or (
            cfg.strategy == "drop_columns" and missing_pct > cfg.threshold
        ):
            dropped_columns.append(col)
            actions[col] = "dropped_column"

        elif strategy == "drop_rows":
            before = len(df)
            df = df.dropna(subset=[col])
            dropped_rows_count += before - len(df)
            actions[col] = "dropped_rows"

        elif strategy == "mean":
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].mean())
                actions[col] = f"filled_mean={round(float(df[col].mean()), 4)}"
            else:
                mode_val = df[col].mode()
                fill = mode_val.iloc[0] if not mode_val.empty else "unknown"
                df[col] = df[col].fillna(fill)
                actions[col] = f"filled_mode(fallback)={fill}"

        elif strategy == "median":
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(df[col].median())
                actions[col] = f"filled_median={round(float(df[col].median()), 4)}"
            else:
                mode_val = df[col].mode()
                fill = mode_val.iloc[0] if not mode_val.empty else "unknown"
                df[col] = df[col].fillna(fill)
                actions[col] = f"filled_mode(fallback)={fill}"

        elif strategy == "mode":
            mode_val = df[col].mode()
            fill = mode_val.iloc[0] if not mode_val.empty else "unknown"
            df[col] = df[col].fillna(fill)
            actions[col] = f"filled_mode={fill}"

        elif strategy == "constant":
            fill = cfg.fill_value if cfg.fill_value is not None else 0
            df[col] = df[col].fillna(fill)
            actions[col] = f"filled_constant={fill}"

        elif strategy == "ffill":
            df[col] = df[col].ffill()
            actions[col] = "forward_filled"

        elif strategy == "bfill":
            df[col] = df[col].bfill()
            actions[col] = "backward_filled"

    if dropped_columns:
        df = df.drop(columns=dropped_columns, errors="ignore")

    return df, {
        "strategy":           cfg.strategy,
        "actions":            actions,
        "dropped_columns":    dropped_columns,
        "dropped_rows_count": dropped_rows_count,
    }


def _resolve_strategy(series: pd.Series, missing_pct: float, cfg: MissingConfig) -> str:
    if cfg.strategy != "auto":
        return cfg.strategy
    # Auto-select
    if missing_pct > cfg.threshold:
        return "drop_columns"
    if pd.api.types.is_numeric_dtype(series):
        return "median"
    return "mode"
