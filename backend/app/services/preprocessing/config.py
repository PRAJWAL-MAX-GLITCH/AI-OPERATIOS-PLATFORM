"""
Preprocessing Pipeline Configuration
=====================================
JSON-serializable config that defines every step of the preprocessing pipeline.
Users submit this config to POST /datasets/{id}/preprocess.

Modes:
  auto   — pipeline auto-selects strategies based on column types
  manual — user specifies every step explicitly
"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Optional


class MissingConfig(BaseModel):
    strategy: Literal[
        "mean", "median", "mode", "constant", "ffill", "bfill",
        "drop_rows", "drop_columns", "auto"
    ] = "auto"
    fill_value: Optional[float | str] = None
    threshold: float = Field(0.5, ge=0.0, le=1.0,
        description="Drop columns with missing% above this when strategy=drop_columns")


class EncodingConfig(BaseModel):
    strategy: Literal[
        "label", "onehot", "ordinal", "frequency", "auto"
    ] = "auto"
    max_cardinality_for_onehot: int = Field(10,
        description="Columns with unique > this get label-encoded instead of OHE")
    drop_first: bool = False


class ScalingConfig(BaseModel):
    strategy: Literal[
        "standard", "minmax", "robust", "maxabs", "normalizer", "none", "auto"
    ] = "auto"


class TransformationConfig(BaseModel):
    apply_log: bool = False
    apply_sqrt: bool = False
    apply_power: bool = False
    apply_yeo_johnson: bool = False
    skew_threshold: float = Field(1.0,
        description="Auto-apply log when skewness > threshold")
    auto_transform_skewed: bool = True


class GenerationConfig(BaseModel):
    polynomial_degree: int = Field(0, ge=0, le=3,
        description="0 = disabled")
    interaction_only: bool = False
    extract_date_features: bool = True
    extract_text_length: bool = True


class SelectionConfig(BaseModel):
    strategy: Literal[
        "variance", "correlation", "kbest", "mutual_info", "none", "auto"
    ] = "auto"
    variance_threshold: float = 0.01
    correlation_threshold: float = 0.95
    k_best: int = Field(20, description="Keep top-k features (kbest/mutual_info)")
    target_column: Optional[str] = None


class PipelineConfig(BaseModel):
    """
    Top-level configuration for a preprocessing pipeline run.
    mode='auto'   → all sub-configs use their 'auto' defaults.
    mode='manual' → user controls every sub-config.
    """
    mode: Literal["auto", "manual"] = "auto"
    target_column: Optional[str] = None
    drop_columns: list[str] = Field(default_factory=list)
    missing:        MissingConfig        = Field(default_factory=MissingConfig)
    encoding:       EncodingConfig       = Field(default_factory=EncodingConfig)
    scaling:        ScalingConfig        = Field(default_factory=ScalingConfig)
    transformation: TransformationConfig = Field(default_factory=TransformationConfig)
    generation:     GenerationConfig     = Field(default_factory=GenerationConfig)
    selection:      SelectionConfig      = Field(default_factory=SelectionConfig)
