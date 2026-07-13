import pytest
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    TestClient fixture for making HTTP requests to the FastAPI app during testing.
    """
    with TestClient(app) as c:
        yield c
