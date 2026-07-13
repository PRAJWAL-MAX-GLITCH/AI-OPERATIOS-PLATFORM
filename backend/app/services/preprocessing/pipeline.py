"""
Preprocessing Pipeline — Main Orchestrator
==========================================
Executes all preprocessing steps in order on a validated DataFrame.
Each step is independent — failures are caught and logged without stopping the pipeline.

Execution order:
  1. Drop user-specified columns
  2. Missing value handling
  3. Feature generation   (before encoding — needs raw strings/dates)
  4. Categorical encoding
  5. Feature transformation
  6. Feature scaling
  7. Feature selection    (last — needs final numeric feature space)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import pandas as pd
import structlog

from app.services.preprocessing.config import PipelineConfig
from app.services.preprocessing.steps.missing       import handle_missing
from app.services.preprocessing.steps.encoding      import encode_categoricals
from app.services.preprocessing.steps.scaling       import scale_features
from app.services.preprocessing.steps.transformation import transform_features
from app.services.preprocessing.steps.generation    import generate_features
from app.services.preprocessing.steps.selection     import select_features

logger = structlog.get_logger(__name__)


@dataclass
class PreprocessingResult:
    dataset_name:  str = ""
    config:        dict[str, Any] = field(default_factory=dict)
    input_shape:   tuple[int, int] = (0, 0)
    output_shape:  tuple[int, int] = (0, 0)
    missing:       dict[str, Any] = field(default_factory=dict)
    generation:    dict[str, Any] = field(default_factory=dict)
    encoding:      dict[str, Any] = field(default_factory=dict)
    transformation: dict[str, Any] = field(default_factory=dict)
    scaling:       dict[str, Any] = field(default_factory=dict)
    selection:     dict[str, Any] = field(default_factory=dict)
    errors:        list[str] = field(default_factory=list)
    warnings:      list[str] = field(default_factory=list)
    output_columns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name":    self.dataset_name,
            "config":          self.config,
            "input_shape":     list(self.input_shape),
            "output_shape":    list(self.output_shape),
            "missing":         self.missing,
            "generation":      self.generation,
            "encoding":        self.encoding,
            "transformation":  self.transformation,
            "scaling":         self.scaling,
            "selection":       self.selection,
            "errors":          self.errors,
            "warnings":        self.warnings,
            "output_columns":  self.output_columns,
        }


def run_preprocessing_pipeline(
    df: pd.DataFrame,
    cfg: PipelineConfig,
    dataset_name: str = "dataset",
) -> tuple[pd.DataFrame, PreprocessingResult]:
    """
    Run the full preprocessing pipeline.
    Returns (processed_dataframe, PreprocessingResult).
    """
    result = PreprocessingResult(
        dataset_name=dataset_name,
        config=cfg.model_dump(),
        input_shape=(len(df), len(df.columns)),
    )

    logger.info("preprocessing_started",
                dataset=dataset_name, rows=len(df), cols=len(df.columns))

    # 0. Drop user-specified columns
    if cfg.drop_columns:
        df = df.drop(columns=cfg.drop_columns, errors="ignore")

    # target column excluded from transformations that would leak it
    target = cfg.target_column

    # 1. Missing values
    df, result.missing = _safe_step("missing", lambda: handle_missing(df, cfg.missing), result)

    # 2. Feature generation (before encoding — raw strings & dates needed)
    df, result.generation = _safe_step("generation",
        lambda: generate_features(df, cfg.generation, exclude_columns=[target] if target else None),
        result)

    # 3. Categorical encoding
    df, result.encoding = _safe_step("encoding",
        lambda: encode_categoricals(df, cfg.encoding),
        result)

    # 4. Feature transformation (apply to numeric after encoding)
    df, result.transformation = _safe_step("transformation",
        lambda: transform_features(df, cfg.transformation, exclude_columns=[target] if target else None),
        result)

    # 5. Scaling
    df, result.scaling = _safe_step("scaling",
        lambda: scale_features(df, cfg.scaling, exclude_columns=[target] if target else None),
        result)

    # 6. Feature selection (last step)
    df, result.selection = _safe_step("selection",
        lambda: select_features(df, cfg.selection, target_col=target),
        result)

    result.output_shape   = (len(df), len(df.columns))
    result.output_columns = list(df.columns)

    logger.info("preprocessing_complete",
                dataset=dataset_name,
                input_shape=result.input_shape,
                output_shape=result.output_shape,
                errors=len(result.errors))

    return df, result


def _safe_step(
    name: str,
    fn,
    result: PreprocessingResult,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Execute a pipeline step, catch exceptions, return (df, metadata)."""
    # We need df from the closure but can't mutate it here, so the lambda captures it.
    # The lambda returns (df, meta) — we split them.
    try:
        out_df, meta = fn()
        return out_df, meta
    except Exception as exc:
        logger.error("preprocessing_step_failed", step=name, error=str(exc))
        result.errors.append(f"{name}: {exc}")
        # Return original df unchanged — fn() has the df in its closure
        # We must return something; caller uses out_df
        raise  # re-raise so caller can handle gracefully


# Patched version that doesn't stop on error:
def run_preprocessing_pipeline(  # noqa: F811  (intentional re-def with error isolation)
    df: pd.DataFrame,
    cfg: PipelineConfig,
    dataset_name: str = "dataset",
) -> tuple[pd.DataFrame, PreprocessingResult]:
    result = PreprocessingResult(
        dataset_name=dataset_name,
        config=cfg.model_dump(),
        input_shape=(len(df), len(df.columns)),
    )

    logger.info("preprocessing_started",
                dataset=dataset_name, rows=len(df), cols=len(df.columns))

    if cfg.drop_columns:
        df = df.drop(columns=cfg.drop_columns, errors="ignore")

    target = cfg.target_column

    def run(stage: str, fn):
        nonlocal df
        try:
            df, meta = fn()
            return meta
        except Exception as exc:
            logger.error("preprocessing_step_failed", step=stage, error=str(exc))
            result.errors.append(f"{stage}: {exc}")
            return {"error": str(exc)}

    result.missing       = run("missing",       lambda: handle_missing(df, cfg.missing))
    result.generation    = run("generation",    lambda: generate_features(df, cfg.generation, [target] if target else None))
    result.encoding      = run("encoding",      lambda: encode_categoricals(df, cfg.encoding))
    result.transformation= run("transformation",lambda: transform_features(df, cfg.transformation, [target] if target else None))
    result.scaling       = run("scaling",       lambda: scale_features(df, cfg.scaling, [target] if target else None))
    result.selection     = run("selection",     lambda: select_features(df, cfg.selection, target))

    result.output_shape   = (len(df), len(df.columns))
    result.output_columns = list(df.columns)

    logger.info("preprocessing_complete",
                dataset=dataset_name,
                output_shape=result.output_shape,
                errors=len(result.errors))

    return df, result
