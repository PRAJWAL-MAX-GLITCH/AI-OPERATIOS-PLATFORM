"""
Feature Engineering & Preprocessing Tests
==========================================
Tests the full pipeline against real datasets:
  - UCI Adult Income   (adult.data — 32,561 rows, 15 cols)
  - Telco Churn        (Telco_customer_churn.xlsx — 7,043 rows, 33 cols)
"""
import pytest
from pathlib import Path
import pandas as pd

from app.services.preprocessing.config import (
    PipelineConfig, MissingConfig, EncodingConfig,
    ScalingConfig, TransformationConfig, SelectionConfig, GenerationConfig,
)
from app.services.preprocessing.pipeline import run_preprocessing_pipeline
from app.services.preprocessing.steps.missing       import handle_missing
from app.services.preprocessing.steps.encoding      import encode_categoricals
from app.services.preprocessing.steps.scaling       import scale_features
from app.services.preprocessing.steps.transformation import transform_features
from app.services.preprocessing.steps.selection     import select_features
from app.services.preprocessing.serializer          import save_pipeline, load_pipeline

ADULT_PATH = Path(r"C:\Users\prajw\Downloads\adult\adult.data")
TELCO_PATH = Path(r"C:\Users\prajw\Downloads\archive (1)\Telco_customer_churn.xlsx")
ADULT_COLS = [
    "age", "workclass", "fnlwgt", "education", "education_num",
    "marital_status", "occupation", "relationship", "race", "sex",
    "capital_gain", "capital_loss", "hours_per_week", "native_country", "income"
]


# ── Fixtures ─────────────────────────────────────────────────────────── #

@pytest.fixture(scope="module")
def adult_df():
    return pd.read_csv(
        ADULT_PATH, header=None, names=ADULT_COLS,
        na_values=["?", "", " "], skipinitialspace=True,
    )

@pytest.fixture(scope="module")
def telco_df():
    return pd.read_excel(TELCO_PATH, engine="openpyxl")

@pytest.fixture(scope="module")
def adult_auto_result(adult_df):
    cfg = PipelineConfig(mode="auto", target_column="income")
    return run_preprocessing_pipeline(adult_df, cfg, dataset_name="adult-income")

@pytest.fixture(scope="module")
def telco_auto_result(telco_df):
    cfg = PipelineConfig(mode="auto")
    return run_preprocessing_pipeline(telco_df, cfg, dataset_name="telco-churn")


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 3: Missing Value Handling                                          #
# ═══════════════════════════════════════════════════════════════════════ #

def test_missing_auto_fills_numerics(adult_df):
    cfg = MissingConfig(strategy="auto")
    out, meta = handle_missing(adult_df, cfg)
    # No nulls should remain in numeric cols after median fill
    assert out["age"].isna().sum() == 0

def test_missing_median_strategy(adult_df):
    cfg = MissingConfig(strategy="median")
    out, meta = handle_missing(adult_df, cfg)
    assert out.isna().sum().sum() == 0

def test_missing_mode_strategy(adult_df):
    cfg = MissingConfig(strategy="mode")
    out, meta = handle_missing(adult_df, cfg)
    assert out.isna().sum().sum() == 0

def test_missing_constant_strategy():
    df = pd.DataFrame({"a": [1.0, None, 3.0], "b": ["x", None, "z"]})
    cfg = MissingConfig(strategy="constant", fill_value=0)
    out, meta = handle_missing(df, cfg)
    assert out["a"].isna().sum() == 0

def test_missing_drop_rows():
    df = pd.DataFrame({"a": [1.0, None, 3.0]})
    cfg = MissingConfig(strategy="drop_rows")
    out, meta = handle_missing(df, cfg)
    assert len(out) == 2
    assert meta["dropped_rows_count"] == 1


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 4: Categorical Encoding                                            #
# ═══════════════════════════════════════════════════════════════════════ #

def test_encoding_onehot_low_cardinality(adult_df):
    # 'sex' has 2 unique values → should be OHE
    cfg = EncodingConfig(strategy="auto", max_cardinality_for_onehot=5)
    out, meta = encode_categoricals(adult_df[["sex", "age"]], cfg)
    # After OHE, 'sex' column is replaced by sex_Female / sex_Male
    assert "sex" not in out.columns
    assert any("sex" in c for c in out.columns)

def test_encoding_label_high_cardinality(adult_df):
    cfg = EncodingConfig(strategy="label")
    out, meta = encode_categoricals(adult_df[["native_country", "age"]], cfg)
    # native_country should be integer now
    assert pd.api.types.is_numeric_dtype(out["native_country"])

def test_encoding_frequency(adult_df):
    cfg = EncodingConfig(strategy="frequency")
    out, meta = encode_categoricals(adult_df[["education", "age"]], cfg)
    # Frequency encoding → values are floats between 0 and 1
    assert pd.api.types.is_float_dtype(out["education"])
    assert out["education"].max() <= 1.0

def test_encoding_no_string_columns_remain_after_auto(adult_df):
    df_copy = adult_df.copy().fillna("unknown")
    cfg = EncodingConfig(strategy="auto", max_cardinality_for_onehot=5)
    out, meta = encode_categoricals(df_copy, cfg)
    remaining_obj = out.select_dtypes(include="object").columns.tolist()
    assert remaining_obj == [], f"String columns remain: {remaining_obj}"


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 5: Feature Scaling                                                 #
# ═══════════════════════════════════════════════════════════════════════ #

def test_scaling_standard(adult_df):
    cfg = ScalingConfig(strategy="standard")
    out, meta = scale_features(adult_df[["age", "fnlwgt"]], cfg)
    # After standard scaling, mean ≈ 0
    assert abs(out["age"].mean()) < 0.01

def test_scaling_minmax(adult_df):
    cfg = ScalingConfig(strategy="minmax")
    out, meta = scale_features(adult_df[["age", "fnlwgt"]], cfg)
    assert out["age"].min() >= -0.01
    assert out["age"].max() <= 1.01

def test_scaling_robust(adult_df):
    cfg = ScalingConfig(strategy="robust")
    out, meta = scale_features(adult_df[["capital_gain"]], cfg)
    # capital_gain has many zeros and outliers — RobustScaler handles this
    assert meta["strategy"] == "robust"
    assert "capital_gain" in meta["scaled_columns"]

def test_scaling_metadata_includes_params(adult_df):
    cfg = ScalingConfig(strategy="standard")
    out, meta = scale_features(adult_df[["age"]], cfg)
    assert "mean" in meta["scaler_params"]
    assert "scale" in meta["scaler_params"]


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 6: Feature Transformation                                          #
# ═══════════════════════════════════════════════════════════════════════ #

def test_transformation_yeo_johnson_reduces_skew(adult_df):
    cfg = TransformationConfig(auto_transform_skewed=True, skew_threshold=1.0)
    before_skew = float(adult_df["capital_gain"].skew())
    out, meta = transform_features(adult_df[["capital_gain"]], cfg)
    after_skew = float(out["capital_gain"].skew())
    # Yeo-Johnson should reduce skewness
    assert abs(after_skew) < abs(before_skew)

def test_transformation_actions_recorded(adult_df):
    cfg = TransformationConfig(auto_transform_skewed=True, skew_threshold=1.0)
    _, meta = transform_features(adult_df[["capital_gain", "capital_loss"]], cfg)
    assert len(meta["transformed_columns"]) > 0


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 8: Feature Selection                                               #
# ═══════════════════════════════════════════════════════════════════════ #

def test_selection_variance_drops_zero_variance():
    import numpy as np
    df = pd.DataFrame({
        "useful": [1, 2, 3, 4, 5],
        "constant": [7, 7, 7, 7, 7],
    })
    cfg = SelectionConfig(strategy="variance", variance_threshold=0.0)
    out, meta = select_features(df, cfg)
    assert "constant" not in out.columns
    assert "useful" in out.columns

def test_selection_correlation_drops_redundant(adult_df):
    cfg = SelectionConfig(strategy="correlation", correlation_threshold=0.95)
    numeric = adult_df.select_dtypes(include="number")
    out, meta = select_features(numeric, cfg)
    assert meta["selected_count"] <= meta["original_count"]

def test_selection_auto_reduces_dimensions(adult_df):
    cfg = SelectionConfig(strategy="auto", variance_threshold=0.01, correlation_threshold=0.95)
    numeric = adult_df.select_dtypes(include="number")
    out, meta = select_features(numeric, cfg)
    assert meta["selected_count"] <= meta["original_count"]


# ═══════════════════════════════════════════════════════════════════════ #
#  Full Pipeline — Adult + Telco                                           #
# ═══════════════════════════════════════════════════════════════════════ #

def test_full_pipeline_adult_no_errors(adult_auto_result):
    df, result = adult_auto_result
    assert len(result.errors) == 0, f"Pipeline errors: {result.errors}"

def test_full_pipeline_adult_reduces_rows_or_keeps(adult_auto_result):
    df, result = adult_auto_result
    # Should have same or fewer rows (drop_rows may remove some)
    assert result.output_shape[0] <= result.input_shape[0]

def test_full_pipeline_adult_output_has_columns(adult_auto_result):
    df, result = adult_auto_result
    assert result.output_shape[1] > 0
    assert len(result.output_columns) == result.output_shape[1]

def test_full_pipeline_telco_no_errors(telco_auto_result):
    df, result = telco_auto_result
    assert len(result.errors) == 0, f"Telco pipeline errors: {result.errors}"

def test_full_pipeline_telco_output_shape(telco_auto_result):
    df, result = telco_auto_result
    assert result.output_shape[0] > 0
    assert result.output_shape[1] > 0


# ═══════════════════════════════════════════════════════════════════════ #
#  STEP 9: Pipeline Serialization                                          #
# ═══════════════════════════════════════════════════════════════════════ #

def test_pipeline_save_and_load(adult_auto_result):
    df, result = adult_auto_result
    path = save_pipeline(result.to_dict(), "test-dataset-id", result.config)
    loaded = load_pipeline(path)
    assert loaded["dataset_id"] == "test-dataset-id"
    assert "result" in loaded
    assert "config" in loaded

def test_pipeline_metadata_contains_all_stages(adult_auto_result):
    df, result = adult_auto_result
    d = result.to_dict()
    for stage in ["missing", "encoding", "scaling", "transformation", "selection"]:
        assert stage in d, f"Stage '{stage}' missing from result dict"


# ═══════════════════════════════════════════════════════════════════════ #
#  API Auth boundaries                                                     #
# ═══════════════════════════════════════════════════════════════════════ #

def test_preprocess_endpoint_requires_auth(client):
    import uuid
    pid = str(uuid.uuid4())
    did = str(uuid.uuid4())
    res = client.post(
        f"/api/v1/projects/{pid}/datasets/{did}/preprocess",
        json={"mode": "auto"},
    )
    assert res.status_code == 401

def test_pipeline_get_requires_auth(client):
    import uuid
    pid = str(uuid.uuid4())
    did = str(uuid.uuid4())
    res = client.get(f"/api/v1/projects/{pid}/datasets/{did}/pipeline")
    assert res.status_code == 401
