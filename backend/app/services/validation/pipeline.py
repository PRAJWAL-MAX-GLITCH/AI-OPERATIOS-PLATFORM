"""
Validation Pipeline — Core Orchestrator
========================================
Runs all validators sequentially on a pandas DataFrame.
Each validator returns a ValidationResult (dict slice).
The pipeline collects all results and passes them to
the QualityScorer to produce a final composite score.

Enterprise pattern: same as Great Expectations / AWS Glue Data Quality.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import pandas as pd
import structlog

from app.services.validation.validators.schema      import validate_schema
from app.services.validation.validators.missing     import analyse_missing
from app.services.validation.validators.duplicates  import analyse_duplicates
from app.services.validation.validators.dtypes      import validate_dtypes
from app.services.validation.validators.numeric     import analyse_numeric
from app.services.validation.validators.categorical import analyse_categorical
from app.services.validation.validators.dates       import analyse_dates
from app.services.validation.validators.outliers    import detect_outliers
from app.services.validation.quality_score          import compute_quality_score

logger = structlog.get_logger(__name__)


@dataclass
class PipelineResult:
    dataset_name: str = ""
    total_rows: int = 0
    total_columns: int = 0
    schema: dict[str, Any]         = field(default_factory=dict)
    missing: dict[str, Any]        = field(default_factory=dict)
    duplicates: dict[str, Any]     = field(default_factory=dict)
    dtypes: dict[str, Any]         = field(default_factory=dict)
    numeric: dict[str, Any]        = field(default_factory=dict)
    categorical: dict[str, Any]    = field(default_factory=dict)
    dates: dict[str, Any]          = field(default_factory=dict)
    outliers: dict[str, Any]       = field(default_factory=dict)
    quality_score: dict[str, Any]  = field(default_factory=dict)
    errors: list[str]              = field(default_factory=list)
    warnings: list[str]            = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_name":   self.dataset_name,
            "total_rows":     self.total_rows,
            "total_columns":  self.total_columns,
            "schema":         self.schema,
            "missing":        self.missing,
            "duplicates":     self.duplicates,
            "dtypes":         self.dtypes,
            "numeric":        self.numeric,
            "categorical":    self.categorical,
            "dates":          self.dates,
            "outliers":       self.outliers,
            "quality_score":  self.quality_score,
            "errors":         self.errors,
            "warnings":       self.warnings,
        }


def run_validation_pipeline(
    df: pd.DataFrame,
    dataset_name: str = "dataset",
    expected_schema: dict[str, str] | None = None,
) -> PipelineResult:
    """
    Execute the full modular validation pipeline on a DataFrame.
    Each stage is independent — one failure does not stop the next.
    """
    result = PipelineResult(
        dataset_name=dataset_name,
        total_rows=len(df),
        total_columns=len(df.columns),
    )

    logger.info("validation_pipeline_started", dataset=dataset_name, rows=len(df), cols=len(df.columns))

    _run(result, "schema",      lambda: validate_schema(df, expected_schema))
    _run(result, "missing",     lambda: analyse_missing(df))
    _run(result, "duplicates",  lambda: analyse_duplicates(df))
    _run(result, "dtypes",      lambda: validate_dtypes(df))
    _run(result, "numeric",     lambda: analyse_numeric(df))
    _run(result, "categorical", lambda: analyse_categorical(df))
    _run(result, "dates",       lambda: analyse_dates(df))
    _run(result, "outliers",    lambda: detect_outliers(df))

    # Final quality score — uses all previous results
    try:
        result.quality_score = compute_quality_score(result)
    except Exception as exc:
        result.errors.append(f"quality_score: {exc}")
        logger.error("validation_stage_failed", stage="quality_score", error=str(exc))

    logger.info(
        "validation_pipeline_complete",
        dataset=dataset_name,
        score=result.quality_score.get("overall_score"),
        errors=len(result.errors),
        warnings=len(result.warnings),
    )
    return result


def _run(result: PipelineResult, stage: str, fn) -> None:
    """Run a single stage, catch exceptions, and store the output."""
    try:
        output = fn()
        setattr(result, stage, output)
        # Bubble up any warnings the stage emitted
        for w in output.get("warnings", []):
            result.warnings.append(f"[{stage}] {w}")
    except Exception as exc:
        result.errors.append(f"{stage}: {exc}")
        logger.error("validation_stage_failed", stage=stage, error=str(exc))
