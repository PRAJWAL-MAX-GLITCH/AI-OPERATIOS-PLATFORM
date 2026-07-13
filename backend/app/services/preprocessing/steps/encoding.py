"""
Categorical Encoder
====================
Supports Label, One-Hot, Ordinal, Frequency encoding.
In 'auto' mode, uses OHE for low-cardinality and Label for high-cardinality columns.
Encoder state (fitted categories) is stored in metadata for pipeline serialization.
"""
from __future__ import annotations
from typing import Any
import pandas as pd
from sklearn.preprocessing import LabelEncoder, OrdinalEncoder
from app.services.preprocessing.config import EncodingConfig


def encode_categoricals(
    df: pd.DataFrame, cfg: EncodingConfig
) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = df.copy()
    cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
    actions: dict[str, Any] = {}
    new_columns: list[str] = []

    for col in cat_cols:
        n_unique = df[col].nunique(dropna=True)
        strategy = _resolve_strategy(n_unique, cfg)

        if strategy == "onehot":
            dummies = pd.get_dummies(
                df[col], prefix=col, drop_first=cfg.drop_first, dtype=int
            )
            df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
            generated = list(dummies.columns)
            new_columns.extend(generated)
            actions[col] = {"strategy": "onehot", "generated_columns": generated}

        elif strategy == "label":
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            actions[col] = {
                "strategy": "label",
                "classes":  list(le.classes_),
            }

        elif strategy == "ordinal":
            oe = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
            df[col] = oe.fit_transform(df[[col]]).astype(int)
            actions[col] = {"strategy": "ordinal"}

        elif strategy == "frequency":
            freq_map = df[col].value_counts(normalize=True).to_dict()
            df[col] = df[col].map(freq_map).fillna(0.0)
            actions[col] = {"strategy": "frequency", "frequencies": {str(k): round(v, 6) for k, v in freq_map.items()}}

    return df, {
        "encoded_columns":   list(actions.keys()),
        "new_columns":       new_columns,
        "actions":           actions,
    }


def _resolve_strategy(n_unique: int, cfg: EncodingConfig) -> str:
    if cfg.strategy != "auto":
        return cfg.strategy
    return "onehot" if n_unique <= cfg.max_cardinality_for_onehot else "label"
