# Enterprise AI Operations Platform

A scalable, production-ready Enterprise AI Operations platform mirroring industry standards (Azure ML, SageMaker, Databricks). 
Built using **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL**, and **Pydantic v2**.

## Architecture & Principles
- **Clean Architecture & Repository Pattern**: Enforces strict separation of concerns between domain models, repositories, services, and API layers.
- **Dependency Injection**: Maximizes testability and modularity.
- **Robust RBAC**: Role-Based Access Control securing everything from projects to dataset usage (`owner`, `admin`, `ml_engineer`, `data_scientist`, `viewer`).
- **Comprehensive Logging**: Structured logging via `structlog`.
- **Validation Gates**: The lifecycle requires datasets to pass **Validation** before **Preprocessing**, and **Preprocessing** before **Training/AutoML**.

---

## Capabilities & Engines

### 1. 🗄️ Core & Dataset Management
- Workspace & Project isolation.
- File upload orchestration & schema inference (CSV, Excel support).
- Automatic Dataset Profiling via Pandas.

### 2. 🛡️ Data Validation Engine
- Runs automated data quality checks *before* data reaches preprocessing or ML layers.
- **Validators Include:** Missing Values, Duplicates, Outliers (Z-score/IQR), Schema Match, Categorical Integrity, DateTime validity.
- Outputs a normalized `quality_score` (0-100) and actionable JSON reports.

### 3. ⚙️ Feature Engineering & Preprocessing Engine
- Consumes *validated* datasets and runs configurable data pipelines.
- Implements:
  - Missing value imputation (mean, median, most_frequent, constant).
  - Categorical encoding (One-Hot, Ordinal, Label).
  - Feature Scaling (Standardization, Min-Max, Robust).
  - Feature Selection (Variance threshold, K-Best).
  - Feature Generation (Polynomials).
  - Transformation (Yeo-Johnson/Box-Cox for skewed distributions).
- Serializes the entire preprocessing state (`joblib`) to guarantee deterministic transformations during inference.

### 4. 🧠 ML Training Engine
- Standardizes algorithm instantiation via a `ModelFactory` pattern.
- Supports Classification (Logistic Regression, Random Forest, Decision Tree, etc.), Regression (Linear, Ridge, etc.), and Clustering (K-Means).
- Implements robust test splitting & stratified sampling.
- Persists models securely to local storage with accompanying JSON metadata payloads.

### 5. 🏆 Model Evaluation & AutoML Engine
- Discovers the best algorithm by cycling through multiple approaches using Out-Of-Fold (OOF) cross-validation.
- Computes comprehensive enterprise metrics:
  - **Classification**: Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, Specificity, Sensitivity, MCC, Cohen's Kappa, Balanced Accuracy.
  - **Regression**: MSE, RMSE, MAE, R², MAPE, Median Absolute Error, Explained Variance.
  - **Clustering**: Silhouette, Davies-Bouldin, Calinski-Harabasz.
- Generates a ranked **Leaderboard**.
- Produces **Stateless Visualizations** (Confusion Matrices, ROC Curves, Residual Plots).

---

## Project Structure
```text
backend/
├── app/
│   ├── api/v1/          # FastAPI Routes (auth, datasets, validation, training, evaluation)
│   ├── core/            # Config, Logging, Exception Handlers, Security
│   ├── models/          # SQLAlchemy Domain Models (Postgres)
│   ├── repositories/    # Database queries and access patterns
│   ├── schemas/         # Pydantic validation schemas
│   └── services/        # Business logic & Pipeline Orchestration
├── data/                # Persisted Datasets, Models, and Pipeline states
├── tests/               # Comprehensive Pytest suites
└── alembic/             # Database Migrations
```

## Running the Platform
1. Create virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt # (or whatever dependency manager is configured)
   ```
2. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Run test suite:
   ```bash
   python -m pytest tests/ -v
   ```

## Documentation
- API Docs (Swagger): `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`