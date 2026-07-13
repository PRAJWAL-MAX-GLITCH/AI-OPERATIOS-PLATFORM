import pytest
from httpx import AsyncClient
from app.main import app
import pytest_asyncio

# We skip real DB integration tests here for brevity in the milestone plan,
# but this demonstrates how the tests are structured to hit the auth endpoints.

@pytest.mark.asyncio
async def test_register_validation_error(client):
    """Test that missing fields raise a 422 Validation Error"""
    response = client.post("/api/v1/auth/register", json={"email": "bademail"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test that bad credentials return a 401 Unauthorized"""
    response = client.post("/api/v1/auth/login", json={
        "email": "notreal@example.com",
        "password": "wrongpassword123"
    })
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"

@pytest.mark.asyncio
async def test_unauthorized_access(client):
    """Test that accessing a protected route without a token fails"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    # OAuth2PasswordBearer returns standard 401 Not authenticated by default
