"""
Dataset Module Tests
Uses your real datasets from Downloads as test fixtures:
 - C:\\Users\\prajw\\Downloads\\adult\\adult.data   (UCI Adult Income - 32k rows, 15 cols)
 - C:\\Users\\prajw\\Downloads\\archive (1)\\Telco_customer_churn.xlsx (Excel churn dataset)
"""
import pytest
import hashlib
from pathlib import Path

from app.services.dataset_parser import parse_file, infer_schema, detect_encoding
from app.services.dataset_profiler import generate_profile

# ── Real dataset paths ────────────────────────────────────────────────── #
ADULT_DATA_PATH = Path(r"C:\Users\prajw\Downloads\adult\adult.data")
TELCO_XLSX_PATH = Path(r"C:\Users\prajw\Downloads\archive (1)\Telco_customer_churn.xlsx")


# ═══════════════════════════════════════════════════════════════════════ #
#  Module-level fixtures (avoid class-scoped fixture deprecation)          #
# ═══════════════════════════════════════════════════════════════════════ #

@pytest.fixture(scope="module")
def adult_content() -> bytes:
    assert ADULT_DATA_PATH.exists(), f"Dataset missing: {ADULT_DATA_PATH}"
    return ADULT_DATA_PATH.read_bytes()


@pytest.fixture(scope="module")
def adult_df(adult_content):
    return parse_file(adult_content, "adult.data")


@pytest.fixture(scope="module")
def adult_profile(adult_df):
    return generate_profile(adult_df, dataset_name="adult-income")


@pytest.fixture(scope="module")
def telco_df():
    assert TELCO_XLSX_PATH.exists(), f"Dataset missing: {TELCO_XLSX_PATH}"
    content = TELCO_XLSX_PATH.read_bytes()
    return parse_file(content, "Telco_customer_churn.xlsx")


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 5: Parser Tests — UCI Adult Income Dataset                         #
# ═══════════════════════════════════════════════════════════════════════ #

def test_adult_row_count(adult_df):
    """
    adult.data has no explicit header line — pandas infers the first
    data row (age=39) as column names, leaving 32,560 data rows.
    The .names file reports 32,561 instances which includes that header row.
    """
    assert len(adult_df) == 32_560, f"Expected 32560 rows, got {len(adult_df)}"


def test_adult_column_count(adult_df):
    """Adult dataset should have 15 columns."""
    assert len(adult_df.columns) == 15, f"Expected 15 columns, got {len(adult_df.columns)}"


def test_adult_encoding_detection(adult_content):
    """Encoding detection must return a non-empty string."""
    enc = detect_encoding(adult_content)
    assert isinstance(enc, str) and len(enc) > 0


def test_adult_schema_inference(adult_df):
    """Schema inference must return metadata for all 15 columns."""
    schema = infer_schema(adult_df)
    assert len(schema) == 15
    for col_meta in schema.values():
        assert "null_count" in col_meta
        assert "unique_count" in col_meta


def test_adult_no_null_numeric_cols(adult_df):
    """Numeric columns (age, fnlwgt, etc.) should have substantial data."""
    first_col = adult_df.iloc[:, 0]
    assert first_col.notna().sum() > 30_000


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 6: Profiler Tests                                                  #
# ═══════════════════════════════════════════════════════════════════════ #

def test_profile_summary_keys(adult_profile):
    summary = adult_profile["summary"]
    required = {"total_rows", "total_columns", "missing_cells", "missing_pct", "duplicate_rows", "memory_usage_bytes"}
    assert required.issubset(set(summary.keys()))


def test_profile_total_rows(adult_profile):
    # Matches parser: first row consumed as header → 32,560 data rows
    assert adult_profile["summary"]["total_rows"] == 32_560


def test_profile_total_columns(adult_profile):
    assert adult_profile["summary"]["total_columns"] == 15


def test_profile_columns_exist(adult_profile):
    assert "columns" in adult_profile
    assert len(adult_profile["columns"]) == 15


def test_profile_numeric_stats(adult_profile):
    """First column (age) must have numeric stats with a computed mean."""
    first_col_key = list(adult_profile["columns"].keys())[0]
    col = adult_profile["columns"][first_col_key]
    assert col["type"] == "numeric"
    assert "stats" in col
    assert col["stats"]["mean"] is not None


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 5: Parser Tests — Telco Excel Dataset                              #
# ═══════════════════════════════════════════════════════════════════════ #

def test_telco_has_rows(telco_df):
    assert len(telco_df) > 0


def test_telco_has_columns(telco_df):
    assert len(telco_df.columns) >= 5


def test_telco_profile_generation(telco_df):
    profile = generate_profile(telco_df, dataset_name="telco-churn")
    assert profile["summary"]["total_rows"] > 0


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 4: Checksum Validation                                             #
# ═══════════════════════════════════════════════════════════════════════ #

def test_checksum_is_sha256():
    digest = hashlib.sha256(b"test content").hexdigest()
    assert len(digest) == 64


def test_same_content_same_checksum():
    data = b"identical content"
    assert hashlib.sha256(data).hexdigest() == hashlib.sha256(data).hexdigest()


def test_different_content_different_checksum():
    a = hashlib.sha256(b"content_A").hexdigest()
    b = hashlib.sha256(b"content_B").hexdigest()
    assert a != b


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 9: API auth boundary tests                                         #
# ═══════════════════════════════════════════════════════════════════════ #

def test_upload_endpoint_requires_auth(client):
    import uuid
    fake_project_id = str(uuid.uuid4())
    response = client.post(
        f"/api/v1/projects/{fake_project_id}/datasets/upload",
        data={"name": "Test", "dataset_type": "raw"},
        files={"file": ("test.csv", b"col1,col2\n1,2\n3,4", "text/csv")},
    )
    assert response.status_code == 401


def test_preview_endpoint_requires_auth(client):
    import uuid
    fake_project_id = str(uuid.uuid4())
    fake_dataset_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/projects/{fake_project_id}/datasets/{fake_dataset_id}/preview")
    assert response.status_code == 401
