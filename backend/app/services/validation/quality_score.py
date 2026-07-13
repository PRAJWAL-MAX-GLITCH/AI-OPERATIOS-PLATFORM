"""
Enterprise Quality Scorer
==========================
Computes a composite Data Quality Score (0–100) across 5 dimensions:

  Completeness  — how complete (non-missing) the data is
  Validity      — schema + dtype compliance
  Uniqueness    — duplicate row / column penalty
  Consistency   — outlier fraction
  Accuracy      — placeholder (requires ground truth)

Final score = weighted average of all dimensions.
Generates human-readable recommendations.
"""
from __future__ import annotations
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.validation.pipeline import PipelineResult

# Weights (must sum to 1.0)
WEIGHTS = {
    "completeness": 0.30,
    "validity":     0.25,
    "uniqueness":   0.20,
    "consistency":  0.20,
    "accuracy":     0.05,  # placeholder
}


def compute_quality_score(result: "PipelineResult") -> dict[str, Any]:
    scores: dict[str, float] = {}

    # ── Completeness (missing values) ────────────────────────── #
    missing_pct = result.missing.get("total_missing_pct", 0) or 0
    scores["completeness"] = max(0.0, 100.0 - missing_pct)

    # ── Validity (schema + dtype issues) ─────────────────────── #
    schema_status = result.schema.get("status", "inferred")
    type_mismatch_count = len(result.schema.get("type_mismatches", []))
    missing_col_count   = len(result.schema.get("missing_columns", []))
    validity_penalty = (type_mismatch_count * 5) + (missing_col_count * 10)
    if schema_status == "failed":
        validity_penalty += 20
    scores["validity"] = max(0.0, 100.0 - validity_penalty)

    # ── Uniqueness (duplicate rows) ──────────────────────────── #
    dup_pct = result.duplicates.get("duplicate_row_pct", 0) or 0
    scores["uniqueness"] = max(0.0, 100.0 - (dup_pct * 2))

    # ── Consistency (outlier density) ────────────────────────── #
    outlier_cols = result.outliers.get("per_column", {})
    if outlier_cols:
        avg_outlier_pct = sum(
            v.get("iqr", {}).get("outlier_pct", 0)
            for v in outlier_cols.values()
        ) / len(outlier_cols)
    else:
        avg_outlier_pct = 0.0
    scores["consistency"] = max(0.0, 100.0 - avg_outlier_pct)

    # ── Accuracy (placeholder) ───────────────────────────────── #
    scores["accuracy"] = 85.0  # placeholder until ground-truth comparison is wired

    # ── Weighted Overall ─────────────────────────────────────── #
    overall = sum(WEIGHTS[dim] * score for dim, score in scores.items())
    overall = round(overall, 2)

    grade = _grade(overall)
    recommendations = _recommendations(scores, result)

    return {
        "overall_score":   overall,
        "grade":           grade,
        "dimension_scores": {k: round(v, 2) for k, v in scores.items()},
        "weights":         WEIGHTS,
        "recommendations": recommendations,
    }


def _grade(score: float) -> str:
    if score >= 90: return "A"
    if score >= 80: return "B"
    if score >= 70: return "C"
    if score >= 60: return "D"
    return "F"


def _recommendations(scores: dict, result: "PipelineResult") -> list[str]:
    recs: list[str] = []

    if scores["completeness"] < 90:
        high = [
            c for c, v in result.missing.get("per_column", {}).items()
            if v["missing_pct"] > 10
        ]
        if high:
            recs.append(f"Impute or drop columns with high missing values: {high[:5]}")

    if scores["uniqueness"] < 90:
        recs.append("Remove or investigate duplicate rows before training.")

    if scores["validity"] < 90:
        mismatches = result.schema.get("type_mismatches", [])
        if mismatches:
            recs.append(f"Fix data type mismatches in: {[m['column'] for m in mismatches[:3]]}")

    if scores["consistency"] < 85:
        recs.append("Investigate outliers — consider capping or log-transforming skewed columns.")

    if not recs:
        recs.append("Dataset quality is good. Proceed to Feature Engineering.")

    return recs
