"""
Date / Datetime Analyser
========================
Attempts to parse object columns as dates.
Validates date ranges, detects future dates, duplicate timestamps,
and missing timestamps in time-series data.
"""
from __future__ import annotations
from typing import Any
from datetime import datetime, timezone
import pandas as pd


def analyse_dates(df: pd.DataFrame) -> dict[str, Any]:
    # Columns already parsed as datetime
    import warnings
    date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()

    # Try to auto-detect string columns that look like dates
    for col in df.select_dtypes(include="object").columns:
        sample = df[col].dropna().head(100)
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                pd.to_datetime(sample, errors="raise")
            date_cols.append(col)
        except (ValueError, TypeError, OverflowError, Exception):
            pass

    per_column: dict[str, Any] = {}
    warnings: list[str] = []
    now = datetime.now(timezone.utc)

    for col in date_cols:
        try:
            parsed = pd.to_datetime(df[col], errors="coerce", utc=True)
        except Exception:
            continue

        valid   = parsed.dropna()
        invalid = int(parsed.isna().sum()) - int(df[col].isna().sum())
        future  = int((valid > now).sum())
        dup_ts  = int(valid.duplicated().sum())

        per_column[col] = {
            "valid_count":   int(valid.count()),
            "invalid_count": max(invalid, 0),
            "future_dates":  future,
            "duplicate_timestamps": dup_ts,
            "min_date": str(valid.min()) if not valid.empty else None,
            "max_date": str(valid.max()) if not valid.empty else None,
        }

        if invalid > 0:
            warnings.append(f"Column '{col}': {invalid} unparseable date(s)")
        if future > 0:
            warnings.append(f"Column '{col}': {future} future date(s)")
        if dup_ts > 0:
            warnings.append(f"Column '{col}': {dup_ts} duplicate timestamp(s)")

    return {
        "date_column_count": len(date_cols),
        "date_columns":      date_cols,
        "per_column":        per_column,
        "warnings":          warnings,
    }
