# Enterprise AI Operations Platform

A scalable, production-ready **Enterprise AI Operations Platform** mirroring industry standards (Azure ML, SageMaker, Databricks, Kubeflow).
Built using **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL**, **MLflow**, and **Pydantic v2**.

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![MLflow](https://img.shields.io/badge/MLflow-Integrated-orange)](https://mlflow.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Architecture & Principles

| Principle | Implementation |
|-----------|---------------|
| **Clean Architecture** | Strict separation of domain models, repositories, services, API layers |
| **Repository Pattern** | All database queries isolated in typed repository classes |
| **Dependency Injection** | FastAPI `Depends()` for DB sessions, services, auth |
| **RBAC** | Role-Based Access Control: `owner`, `admin`, `ml_engineer`, `data_scientist`, `viewer` |
| **Structured Logging** | `structlog` with JSON output for every service and pipeline |
| **Validation Gates** | `Dataset → Validation → Preprocessing → Training → AutoML → Registry → Serving` |

---

## 🔋 Platform Engines

### 1. 🗄️ Core & Dataset Management
- Multi-tenant **Workspace & Project** isolation.
- File upload orchestration & schema inference (CSV, Excel support).
- Automatic **Dataset Profiling** via Pandas (column types, nulls, cardinality).

### 2. 🛡️ Data Validation Engine
- Automated quality checks **before** any dataset reaches the ML pipeline.
- **Validators:** Missing Values, Duplicates, Outliers (Z-score/IQR), Schema Match, Categorical Integrity, DateTime validity.
- Outputs a normalized `quality_score` (0–100) + actionable JSON report.

### 3. ⚙️ Feature Engineering & Preprocessing Engine
- Consumes **validated-only** datasets.
- Configurable pipeline supporting:
  - **Imputation:** mean, median, most_frequent, constant.
  - **Encoding:** One-Hot, Ordinal, Label.
  - **Scaling:** Standardization, Min-Max, Robust.
  - **Selection:** Variance threshold, K-Best.
  - **Generation:** Polynomial features.
  - **Transformation:** Yeo-Johnson / Box-Cox.
- Serializes pipeline state via `joblib` for deterministic inference.

### 4. 🧠 ML Training Engine
- Standardizes algorithm instantiation via a **ModelFactory** pattern.
- Supports **Classification** (Logistic Regression, Random Forest, Decision Tree, SVM, Gradient Boosting, XGBoost), **Regression** (Linear, Ridge, Lasso, ElasticNet), and **Clustering** (K-Means).
- Stratified train/test splitting & robust metric collection.
- Persists trained models locally with JSON metadata.

### 5. 🏆 Model Evaluation & AutoML Engine
- Cycles through all algorithms with **Out-of-Fold (OOF) cross-validation**.
- Enterprise metric suite:
  - **Classification:** Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Specificity, Sensitivity, MCC, Cohen's Kappa, Balanced Accuracy.
  - **Regression:** MSE, RMSE, MAE, R², MAPE, Median Absolute Error, Explained Variance.
  - **Clustering:** Silhouette, Davies-Bouldin, Calinski-Harabasz.
- Ranked **Leaderboard** & automated best-model selection.
- Stateless visualizations: Confusion Matrices, ROC Curves, Residual Plots (Base64-encoded).

### 6. 🔬 MLOps & Experiment Tracking (MLflow)
- Full **MLflow integration** — tracking URI, SQLite backend, artifact store.
- Every training run and AutoML evaluation is automatically logged:
  - Metrics, hyperparameters, dataset tags, algorithm tags.
  - Model artifacts bundled with `conda.yaml` and `python_env.yaml`.
- **Model Registry** with lifecycle stages: `None → Staging → Production → Archived`.
- REST APIs for registry inspection & stage transitions (`POST /mlops/models/{name}/stage`).

### 7. 🚀 Enterprise Prediction & Model Serving
- **Online Inference** — sub-millisecond LRU-cached model loading. Serving up to 10 models in memory simultaneously.
- **SHAP Explainability** — per-prediction feature contribution scores + Base64 Waterfall plots embedded directly in the API response JSON.
- **Prediction History** — every inference is logged to Postgres (model version, latency_ms, confidence, input payload, explanation).
- REST APIs: `POST /predict`, `GET /predictions`.

---

## Project Structure

```text
backend/
├── app/
│   ├── api/v1/                  # FastAPI Routes
│   │   ├── auth.py              # Authentication
│   │   ├── datasets.py          # Dataset management
│   │   ├── validation.py        # Data validation
│   │   ├── preprocessing.py     # Feature engineering
│   │   ├── training.py          # ML training
│   │   ├── evaluation.py        # AutoML evaluation
│   │   ├── mlops.py             # MLflow model registry
│   │   └── serving.py           # Prediction & serving
│   ├── core/                    # Config, Logging, Exceptions, Security
│   ├── models/                  # SQLAlchemy Domain Models
│   ├── repositories/            # Data access patterns
│   ├── schemas/                 # Pydantic v2 schemas
│   └── services/
│       ├── mlops/               # MLflow tracker & registry wrappers
│       └── serving/             # Model loader, explainer, prediction pipeline
├── data/
│   ├── mlflow.db                # MLflow SQLite tracking backend
│   ├── mlruns/                  # MLflow artifact store
│   └── models/                  # Serialized sklearn models
├── tests/
│   └── api/                     # Pytest integration test suites
└── alembic/                     # Database migrations
```

---

## 🔗 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | Authenticate & get JWT token |
| `POST` | `/api/v1/projects/{id}/datasets/upload` | Upload dataset |
| `POST` | `/api/v1/projects/{id}/datasets/{id}/validate` | Run data validation |
| `POST` | `/api/v1/projects/{id}/datasets/{id}/preprocess` | Run preprocessing |
| `POST` | `/api/v1/projects/{id}/datasets/{id}/train` | Start training job |
| `POST` | `/api/v1/projects/{id}/datasets/{id}/evaluate` | Start AutoML evaluation |
| `GET`  | `/api/v1/mlops/models` | List registered models |
| `POST` | `/api/v1/mlops/models/{name}/stage` | Transition model stage |
| `POST` | `/api/v1/projects/{id}/models/{name}/predict` | Online inference + XAI |
| `GET`  | `/api/v1/projects/{id}/models/{name}/predictions` | Prediction history |

---

## 🚀 Running the Platform

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env          # Set DATABASE_URL, JWT_SECRET_KEY, etc.

# 3. Run database migrations
python -m alembic upgrade head

# 4. Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 5. Run the full test suite
python -m pytest tests/ -v
```

---

## 📚 Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **MLflow UI**: `mlflow ui --backend-store-uri sqlite:///data/mlflow.db`

---

## 🧪 Test Coverage

| Module | Test File |
|--------|-----------|
| Data Validation | `tests/api/test_validation.py` |
| Feature Engineering | `tests/api/test_preprocessing.py` |
| ML Training | `tests/api/test_training.py` |
| AutoML Evaluation | `tests/api/test_evaluation.py` |
| MLOps / Registry | `tests/api/test_mlops.py` |
| Prediction & XAI | `tests/api/test_serving.py` |

---

## 🏗️ Milestones Completed

| # | Milestone | Status |
|---|-----------|--------|
| 1 | Foundation (FastAPI, PostgreSQL, JWT, RBAC) | ✅ |
| 2 | Dataset Management & Profiling | ✅ |
| 3 | Data Validation Engine | ✅ |
| 4 | Feature Engineering & Preprocessing | ✅ |
| 5 | ML Training Engine (ModelFactory) | ✅ |
| 6 | Model Evaluation & AutoML Engine | ✅ |
| 7 | MLOps & Experiment Tracking (MLflow) | ✅ |
| 8 | Prediction & Model Serving (XAI/SHAP) | ✅ |