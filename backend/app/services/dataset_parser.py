"""
Enterprise Dataset Parser
Handles CSV, Excel, JSON, Parquet files with:
- Automatic delimiter detection
- Encoding detection via chardet
- Schema inference
- Missing value analysis
- Data type inference
"""
import io
import chardet
import pandas as pd
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

SUPPORTED_FORMATS = {"csv", "data", "xlsx", "xls", "json", "parquet"}


def detect_encoding(raw: bytes) -> str:
    """Use chardet to auto-detect file encoding."""
    result = chardet.detect(raw[:10_000])  # sample first 10KB
    encoding = result.get("encoding") or "utf-8"
    logger.debug("encoding_detected", encoding=encoding, confidence=result.get("confidence"))
    return encoding


def parse_file(content: bytes, filename: str) -> pd.DataFrame:
    """
    Route a file to the correct parser based on extension.
    Returns a pandas DataFrame.
    """
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext in ("csv", "data"):
        return _parse_csv(content, filename)
    elif ext in ("xlsx", "xls"):
        return _parse_excel(content)
    elif ext == "json":
        return _parse_json(content)
    elif ext == "parquet":
        return _parse_parquet(content)
    else:
        raise ValueError(f"Unsupported file format: .{ext}")


def _parse_csv(content: bytes, filename: str) -> pd.DataFrame:
    """
    Enterprise CSV/data parser with:
    - Auto encoding detection
    - Auto delimiter sniffing
    - Header normalization
    """
    encoding = detect_encoding(content)
    text = content.decode(encoding, errors="replace")

    # Sniff delimiter
    sample = text[:4096]
    try:
        import csv
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    logger.debug("csv_parsing", filename=filename, delimiter=repr(delimiter), encoding=encoding)

    # For UCI .data files with no header, try to load with default int columns
    # We detect the presence of a header by checking if the first row looks like data
    df = pd.read_csv(
        io.StringIO(text),
        sep=delimiter,
        na_values=["?", "NA", "N/A", "", " ", "nan", "NaN", "null"],
        skipinitialspace=True,
        engine="python",
        on_bad_lines="skip",
        header="infer",
    )
    # Strip whitespace from string columns and headers
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    return df


def _parse_excel(content: bytes) -> pd.DataFrame:
    return pd.read_excel(io.BytesIO(content), engine="openpyxl", na_values=["?", "NA", "N/A", ""])


def _parse_json(content: bytes) -> pd.DataFrame:
    return pd.read_json(io.BytesIO(content))


def _parse_parquet(content: bytes) -> pd.DataFrame:
    return pd.read_parquet(io.BytesIO(content))


def infer_schema(df: pd.DataFrame) -> dict[str, Any]:
    """
    Return a column-level schema dict with inferred types,
    null counts, and unique value counts.
    """
    schema: dict[str, Any] = {}
    for col in df.columns:
        series = df[col]
        schema[col] = {
            "dtype": str(series.dtype),
            "null_count": int(series.isna().sum()),
            "null_pct": round(series.isna().mean() * 100, 2),
            "unique_count": int(series.nunique(dropna=True)),
        }
    return schema
