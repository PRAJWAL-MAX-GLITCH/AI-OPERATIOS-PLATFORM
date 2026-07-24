# Enterprise AI Operations Platform

A scalable, production-ready **Enterprise AI Operations Platform** mirroring industry standards (Azure ML, SageMaker, Databricks, LangChain, Kubeflow).
Built using **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL**, **MLflow**, **Pydantic v2**, and a **React + Tailwind** frontend.

[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-blue)](https://react.dev)
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
| **Structured Logging** | `structlog` + OpenTelemetry for distributed tracing and monitoring |
| **Validation Gates** | `Dataset → Validation → Preprocessing → Training → AutoML → Registry → Serving` |

---

## 🔋 Platform Engines

### 1. 🗄️ Core & Dataset Management
- Multi-tenant **Workspace & Project** isolation.
- File upload orchestration & schema inference (CSV, Excel support).
- Automatic **Dataset Profiling** via Pandas (column types, nulls, cardinality).

### 2. 🛡️ Data Validation & Quality
- Automated quality checks before any dataset reaches the ML pipeline.
- Outputs a normalized `quality_score` (0–100) + actionable JSON report.

### 3. 🤖 Generative AI & RAG Engine
- **Vector Database Integration:** Qdrant/ChromaDB for semantic search.
- **RAG Pipelines:** Automated PDF/Doc ingestion, chunking, and embedding generation.
- **Agentic Workflows:** LangGraph-based agents for autonomous task execution and tool-calling.
- **Chat Interface:** State-aware chat sessions with history and context retrieval.

### 4. ⚙️ Feature Engineering & Training
- Configurable pipelines for Scikit-learn, XGBoost, and PyTorch.
- **MLOps:** Full MLflow integration for experiment tracking, artifact versioning, and registry lifecycle management.

### 5. 📈 Monitoring & Observability
- **Real-time Metrics:** Prometheus/Grafana integration for system/model performance.
- **Observability:** Arize/LangSmith tracing for GenAI latency, token usage, and LLM output quality monitoring.

### 6. 🚀 Enterprise Serving & Frontend
- **Model/LLM Serving:** FastAPI high-concurrency endpoints with SHAP explainability.
- **Premium React Frontend:** Comprehensive modern Dashboard featuring a high-end SaaS aesthetic, slate/zinc color system, and redesigned UI components for workspace management, experiment tracking, and real-time chat/agent visualization.

---

## Project Structure

```text
root/
├── backend/                  # FastAPI Core
│   ├── app/
│   │   ├── api/             # V1 Endpoints (Auth, ML, GenAI, Chat)
│   │   ├── core/            # Config, Security, OTel Monitoring
│   │   ├── services/        # RAG, Agents, MLflow, Serving, Workflows
│   │   └── models/          # SQLAlchemy & Pydantic
├── frontend/                 # React + Tailwind Dashboard
│   ├── src/
│   │   ├── components/      # UI components, Chat, Leaderboard
│   │   └── hooks/           # API integration hooks
├── data/                     # MLflow db, Vector DB storage
└── alembic/                  # Database migrations
```

---

## 🔗 Key API Capabilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/login` | JWT Authentication |
| `POST` | `/api/v1/rag/ingest` | Process documents into Vector DB |
| `POST` | `/api/v1/chat/completions` | Chat with Agentic context |
| `POST` | `/api/v1/projects/{id}/train` | ML training job |
| `GET`  | `/api/v1/monitoring/traces` | Observability data |

---

## 🚀 Running the Platform

```bash
# 1. Setup Backend
cd backend && pip install -r requirements.txt
python -m alembic upgrade head

# 2. Setup Frontend
cd frontend && npm install && npm run dev

# 3. Launch Services
uvicorn app.main:app --reload
```

---

## 🏗️ Milestones Completed

| # | Milestone | Status |
|---|-----------|--------|
| 1 | Foundation (FastAPI, PostgreSQL, RBAC) | ✅ |
| 2 | ML Pipeline (Training, Registry, Serving) | ✅ |
| 3 | GenAI (RAG, Embeddings, Vector Search) | ✅ |
| 4 | Agentic Workflows (LangGraph) | ✅ |
| 5 | Monitoring & Observability (OTel/Prometheus) | ✅ |
| 6 | React Frontend Dashboard | ✅ |