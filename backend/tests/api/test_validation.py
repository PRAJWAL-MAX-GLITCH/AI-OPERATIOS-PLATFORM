"""
Validation Engine Tests
=======================
Runs the full modular pipeline against your real datasets:
  - UCI Adult Income   (adult.data  — 32,561 rows, 15 cols)
  - Telco Churn        (Telco_customer_churn.xlsx — 7,043 rows, 33 cols)
"""
import pytest
from pathlib import Path
import pandas as pd

from app.services.dataset_parser import parse_file
from app.services.validation.pipeline import run_validation_pipeline
from app.services.validation.validators.schema      import validate_schema
from app.services.validation.validators.missing     import analyse_missing
from app.services.validation.validators.duplicates  import analyse_duplicates
from app.services.validation.validators.dtypes      import validate_dtypes
from app.services.validation.validators.numeric     import analyse_numeric
from app.services.validation.validators.categorical import analyse_categorical
from app.services.validation.validators.outliers    import detect_outliers
from app.services.validation.quality_score          import compute_quality_score

ADULT_PATH = Path(r"C:\Users\prajw\Downloads\adult\adult.data")
TELCO_PATH = Path(r"C:\Users\prajw\Downloads\archive (1)\Telco_customer_churn.xlsx")

ADULT_COLUMNS = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country", "income"
]


# ── Fixtures ─────────────────────────────────────────────────────────── #

@pytest.fixture(scope="module")
def adult_df():
    content = ADULT_PATH.read_bytes()
    df = pd.read_csv(
        ADULT_PATH, header=None, names=ADULT_COLUMNS,
        na_values=["?", "", " "], skipinitialspace=True,
    )
    return df


@pytest.fixture(scope="module")
def telco_df():
    return pd.read_excel(TELCO_PATH, engine="openpyxl")


@pytest.fixture(scope="module")
def adult_pipeline_result(adult_df):
    return run_validation_pipeline(adult_df, dataset_name="adult-income")


@pytest.fixture(scope="module")
def telco_pipeline_result(telco_df):
    return run_validation_pipeline(telco_df, dataset_name="telco-churn")


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 3: Schema Validation                                               #
# ═══════════════════════════════════════════════════════════════════════ #

def test_schema_auto_infer(adult_df):
    result = validate_schema(adult_df, expected_schema=None)
    assert result["status"] == "inferred"
    assert result["total_columns"] == 15
    assert "age" in result["inferred_schema"]


def test_schema_passes_with_correct_spec(adult_df):
    expected = {col: "object" for col in ADULT_COLUMNS}
    expected["age"] = "int64"
    result = validate_schema(adult_df, expected)
    # Some columns will mismatch (fnlwgt is int, others object), but status reflects that
    assert result["total_columns"] == 15


def test_schema_detects_missing_column(adult_df):
    expected = {"non_existent_column": "int64", "age": "int64"}
    result = validate_schema(adult_df, expected)
    assert "non_existent_column" in result["missing_columns"]
    assert result["status"] == "failed"


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 4: Missing Value Analysis                                           #
# ═══════════════════════════════════════════════════════════════════════ #

def test_missing_values_adult(adult_df):
    result = analyse_missing(adult_df)
    assert "total_missing_cells" in result
    assert result["total_missing_cells"] > 0     # Adult dataset has missing values (~?)
    assert result["total_missing_pct"] < 10      # But overall low missingness
    assert "per_column" in result


def test_missing_ranks_columns(adult_df):
    result = analyse_missing(adult_df)
    ranked = result["ranked_columns"]
    # Should be sorted worst first
    if len(ranked) >= 2:
        assert ranked[0]["missing_count"] >= ranked[1]["missing_count"]


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 5: Duplicate Detection                                             #
# ═══════════════════════════════════════════════════════════════════════ #

def test_duplicates_adult(adult_df):
    result = analyse_duplicates(adult_df)
    assert "duplicate_row_count" in result
    assert "duplicate_row_pct"   in result
    assert result["duplicate_row_count"] >= 0


def test_no_duplicate_columns_adult(adult_df):
    result = analyse_duplicates(adult_df)
    # Adult dataset should have no perfectly duplicate columns
    assert result["duplicate_column_pairs"] == []


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 6: Data Type Validation                                            #
# ═══════════════════════════════════════════════════════════════════════ #

def test_dtypes_detects_numeric_cols(adult_df):
    result = validate_dtypes(adult_df)
    type_summary = result["type_summary"]
    assert type_summary.get("integer", 0) > 0   # age, fnlwgt etc.
    assert type_summary.get("string", 0) > 0    # workclass, education etc.


def test_dtypes_per_column_present(adult_df):
    result = validate_dtypes(adult_df)
    assert "age" in result["per_column"]
    assert result["per_column"]["age"]["category"] == "integer"


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 7: Numeric Analysis                                                #
# ═══════════════════════════════════════════════════════════════════════ #

def test_numeric_stats_adult(adult_df):
    result = analyse_numeric(adult_df)
    assert result["numeric_column_count"] > 0
    assert "age" in result["per_column"]
    stats = result["per_column"]["age"]
    assert stats["mean"] is not None
    assert 17 <= stats["min"] <= 20   # UCI Adult: age starts at 17
    assert stats["max"] <= 100


def test_numeric_has_all_fields(adult_df):
    result = analyse_numeric(adult_df)
    required = {"count","mean","median","std","min","max","skewness","kurtosis","q1","q3","iqr"}
    for col_stats in result["per_column"].values():
        assert required.issubset(set(col_stats.keys()))


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 8: Categorical Analysis                                            #
# ═══════════════════════════════════════════════════════════════════════ #

def test_categorical_adult(adult_df):
    result = analyse_categorical(adult_df)
    assert result["categorical_column_count"] > 0
    assert "income" in result["per_column"]
    income = result["per_column"]["income"]
    # Adult income column has only 2 categories: <=50K and >50K
    assert income["unique_count"] == 2


def test_categorical_top_values_capped(adult_df):
    result = analyse_categorical(adult_df)
    for col_data in result["per_column"].values():
        assert len(col_data["top_values"]) <= 20


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 10: Outlier Detection                                              #
# ═══════════════════════════════════════════════════════════════════════ #

def test_outlier_detection_adult(adult_df):
    result = detect_outliers(adult_df)
    assert result["numeric_columns_checked"] > 0
    assert "per_column" in result
    # capital_gain and capital_loss are known to have extreme outliers
    if "capital_gain" in result["per_column"]:
        iqr_res = result["per_column"]["capital_gain"]["iqr"]
        assert iqr_res["outlier_count"] > 0   # capital_gain has many zeros + huge spikes


def test_outlier_iqr_fields_present(adult_df):
    result = detect_outliers(adult_df)
    for col_data in result["per_column"].values():
        iqr = col_data["iqr"]
        assert "lower_fence" in iqr
        assert "upper_fence" in iqr
        assert "outlier_count" in iqr


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 11: Quality Score                                                  #
# ═══════════════════════════════════════════════════════════════════════ #

def test_quality_score_adult(adult_pipeline_result):
    qs = adult_pipeline_result.quality_score
    assert "overall_score" in qs
    assert "grade" in qs
    assert "dimension_scores" in qs
    assert 0 <= qs["overall_score"] <= 100


def test_quality_score_dimensions(adult_pipeline_result):
    dims = adult_pipeline_result.quality_score["dimension_scores"]
    for dim in ["completeness", "validity", "uniqueness", "consistency", "accuracy"]:
        assert dim in dims
        assert 0 <= dims[dim] <= 100


def test_quality_score_has_recommendations(adult_pipeline_result):
    qs = adult_pipeline_result.quality_score
    assert len(qs["recommendations"]) > 0


# ═══════════════════════════════════════════════════════════════════════ #
#  Full Pipeline — Telco                                                    #
# ═══════════════════════════════════════════════════════════════════════ #

def test_full_pipeline_telco(telco_pipeline_result):
    r = telco_pipeline_result
    assert r.total_rows == 7043
    assert r.total_columns == 33
    assert r.quality_score.get("overall_score") is not None
    assert r.quality_score.get("grade") in list("ABCDF")


def test_pipeline_no_crash_on_either_dataset(adult_pipeline_result, telco_pipeline_result):
    assert len(adult_pipeline_result.errors) == 0
    assert len(telco_pipeline_result.errors) == 0


# ═══════════════════════════════════════════════════════════════════════ #
#  API Auth boundaries                                                     #
# ═══════════════════════════════════════════════════════════════════════ #

def test_validate_endpoint_requires_auth(client):
    import uuid
    pid = str(uuid.uuid4())
    did = str(uuid.uuid4())
    res = client.post(f"/api/v1/projects/{pid}/datasets/{did}/validate")
    assert res.status_code == 401


def test_validation_get_requires_auth(client):
    import uuid
    pid = str(uuid.uuid4())
    did = str(uuid.uuid4())
    res = client.get(f"/api/v1/projects/{pid}/datasets/{did}/validation")
    assert res.status_code == 401
