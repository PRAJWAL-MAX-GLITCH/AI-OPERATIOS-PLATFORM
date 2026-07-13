"""
Feature Generator
==================
Creates new features from existing ones:
  - Date decomposition (year, month, day, hour, weekday, quarter)
  - Text length features for string columns
  - Polynomial & interaction features (configurable degree)
  - Interaction pairs (col_a * col_b)
"""
from __future__ import annotations
from typing import Any
import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from app.services.preprocessing.config import GenerationConfig


def generate_features(
    df: pd.DataFrame,
    cfg: GenerationConfig,
    exclude_columns: list[str] | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = df.copy()
    exclude = set(exclude_columns or [])
    new_features: list[str] = []
    actions: list[str] = []

    # ── Date features ───────────────────────────────────────── #
    if cfg.extract_date_features:
        date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
        for col in date_cols:
            if col in exclude:
                continue
            for part, fn in [
                ("year",    lambda s: s.dt.year),
                ("month",   lambda s: s.dt.month),
                ("day",     lambda s: s.dt.day),
                ("hour",    lambda s: s.dt.hour),
                ("weekday", lambda s: s.dt.weekday),
                ("quarter", lambda s: s.dt.quarter),
            ]:
                new_col = f"{col}__{part}"
                df[new_col] = fn(df[col])
                new_features.append(new_col)
            actions.append(f"date_features from '{col}'")

    # ── Text length features ─────────────────────────────────── #
    if cfg.extract_text_length:
        str_cols = df.select_dtypes(include="object").columns
        for col in str_cols:
            if col in exclude:
                continue
            new_col = f"{col}__length"
            df[new_col] = df[col].astype(str).str.len()
            new_features.append(new_col)
        if list(str_cols):
            actions.append(f"text_length for {list(str_cols)}")

    # ── Polynomial features ──────────────────────────────────── #
    if cfg.polynomial_degree >= 2:
        num_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c not in exclude and c not in new_features
        ][:10]  # cap at 10 to avoid explosion
        if num_cols:
            pf = PolynomialFeatures(
                degree=cfg.polynomial_degree,
                interaction_only=cfg.interaction_only,
                include_bias=False,
            )
            poly_arr = pf.fit_transform(df[num_cols].fillna(0))
            poly_names = pf.get_feature_names_out(num_cols)
            # Only add the new derived ones (skip originals)
            original_set = set(num_cols)
            for name, col_arr in zip(poly_names, poly_arr.T):
                if name not in original_set:
                    df[name] = col_arr
                    new_features.append(name)
            actions.append(
                f"polynomial_degree={cfg.polynomial_degree} on {len(num_cols)} cols → {len(poly_names)} features"
            )

    return df, {
        "new_feature_count": len(new_features),
        "new_features":      new_features[:50],  # cap log size
        "actions":           actions,
    }
