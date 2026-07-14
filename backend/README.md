# Enterprise AI Operations Platform - Backend

This is the foundational backend for the Enterprise AI Operations Platform, built with FastAPI.

## Requirements
- Python 3.11+
- Poetry (for dependency management)
- Docker (optional, for local infrastructure)
- Data preprocessing & Validation
- Traditional ML & Deep Learning (PyTorch)
- Retrieval-Augmented Generation (RAG)

To initialize the API backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python run.py
```

## How to Add Documents for RAG

To leverage the Enterprise Retrieval-Augmented Generation (RAG) engine:

1. **Place your documents**: Copy any supported files (PDF, DOCX, TXT, MD, HTML) into the `backend/documents/` directory.
2. **Trigger Indexing**: Call the POST API endpoint to index the documents.
   - Endpoint: `POST /api/v1/rag/knowledge-bases/{kb_id}/index`
   - This single command will automatically discover, parse, clean, chunk, generate embeddings (SentenceTransformers), and build the FAISS index.
3. **Verify Indexing**: Check the API response to see the generated `IndexingReportResponse` containing the number of chunks and total documents successfully ingested.
4. **Search**: Query the knowledge base via `POST /api/v1/rag/knowledge-bases/{kb_id}/search`.

## Installation

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Copy environment file:
   ```bash
   cp .env.example .env
   ```

3. Run the application:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## Development
- **Tests**: `poetry run pytest`
- **Linting**: `poetry run ruff check .`
- **Formatting**: `poetry run black .`
- **Type Checking**: `poetry run mypy .`
