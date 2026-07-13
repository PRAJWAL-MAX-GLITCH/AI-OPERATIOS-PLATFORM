"""
Feature Selector
================
Multiple strategies for dimensionality reduction:
  variance   — drop near-zero-variance features
  correlation — drop one of highly correlated pairs
  kbest       — SelectKBest with ANOVA F-test
  mutual_info — mutual information score
  auto        — runs variance + correlation in sequence
"""
from __future__ import annotations
from typing import Any
import pandas as pd
import numpy as np
from sklearn.feature_selection import (
    VarianceThreshold, SelectKBest, f_classif, mutual_info_classif
)
from app.services.preprocessing.config import SelectionConfig


def select_features(
    df: pd.DataFrame,
    cfg: SelectionConfig,
    target_col: str | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = df.copy()
    original_cols = list(df.columns)
    dropped: list[str] = []
    actions: list[str] = []

    strategy = cfg.strategy

    # Drop target from feature matrix for selection
    X = df.drop(columns=[target_col], errors="ignore") if target_col else df
    y = df[target_col] if target_col and target_col in df.columns else None

    if strategy in ("variance", "auto"):
        X, d = _variance_filter(X, cfg.variance_threshold)
        dropped.extend(d)
        actions.append(f"variance_threshold={cfg.variance_threshold}: dropped {len(d)} cols")

    if strategy in ("correlation", "auto"):
        X, d = _correlation_filter(X, cfg.correlation_threshold)
        dropped.extend(d)
        actions.append(f"correlation_threshold={cfg.correlation_threshold}: dropped {len(d)} cols")

    if strategy == "kbest" and y is not None:
        X, d = _kbest_filter(X, y, cfg.k_best)
        dropped.extend(d)
        actions.append(f"kbest={cfg.k_best}")

    if strategy == "mutual_info" and y is not None:
        X, d = _mutual_info_filter(X, y, cfg.k_best)
        dropped.extend(d)
        actions.append(f"mutual_info top-{cfg.k_best}")

    # Re-attach target
    if target_col and target_col in df.columns and target_col not in X.columns:
        X[target_col] = df[target_col]

    return X, {
        "strategy":        strategy,
        "original_count":  len(original_cols),
        "selected_count":  len(X.columns),
        "dropped_count":   len(dropped),
        "dropped_columns": dropped,
        "actions":         actions,
    }


def _variance_filter(X: pd.DataFrame, threshold: float) -> tuple[pd.DataFrame, list[str]]:
    numeric = X.select_dtypes(include=[np.number])
    if numeric.empty:
        return X, []
    sel = VarianceThreshold(threshold=threshold)
    sel.fit(numeric.fillna(0))
    low_var = [c for c, s in zip(numeric.columns, sel.variances_) if s <= threshold]
    return X.drop(columns=low_var, errors="ignore"), low_var


def _correlation_filter(X: pd.DataFrame, threshold: float) -> tuple[pd.DataFrame, list[str]]:
    numeric = X.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        return X, []
    corr = numeric.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    to_drop = [c for c in upper.columns if any(upper[c] > threshold)]
    return X.drop(columns=to_drop, errors="ignore"), to_drop


def _kbest_filter(X: pd.DataFrame, y: pd.Series, k: int) -> tuple[pd.DataFrame, list[str]]:
    numeric = X.select_dtypes(include=[np.number]).fillna(0)
    if numeric.empty or len(numeric.columns) <= k:
        return X, []
    k = min(k, len(numeric.columns))
    sel = SelectKBest(f_classif, k=k)
    sel.fit(numeric, y)
    keep = numeric.columns[sel.get_support()].tolist()
    drop = [c for c in numeric.columns if c not in keep]
    return X.drop(columns=drop, errors="ignore"), drop


def _mutual_info_filter(X: pd.DataFrame, y: pd.Series, k: int) -> tuple[pd.DataFrame, list[str]]:
    numeric = X.select_dtypes(include=[np.number]).fillna(0)
    if numeric.empty or len(numeric.columns) <= k:
        return X, []
    k = min(k, len(numeric.columns))
    scores = mutual_info_classif(numeric, y, random_state=42)
    ranked = sorted(zip(numeric.columns, scores), key=lambda x: x[1], reverse=True)
    keep = {c for c, _ in ranked[:k]}
    drop = [c for c in numeric.columns if c not in keep]
    return X.drop(columns=drop, errors="ignore"), drop
