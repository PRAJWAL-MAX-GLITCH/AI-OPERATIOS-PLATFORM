# Enterprise AI Operations Platform - Backend

This is the foundational backend for the Enterprise AI Operations Platform, built with FastAPI.

## Requirements
- Python 3.11+
- Poetry (for dependency management)
- Docker (optional, for local infrastructure)

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
