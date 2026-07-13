from fastapi.testclient import TestClient

def test_health_endpoint(client: TestClient) -> None:
    """
    Test that the health check endpoint returns 200 OK and the correct structure.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    json_data = response.json()
    assert "data" in json_data
    assert json_data["data"]["status"] == "ok"
    assert json_data["data"]["service"] == "enterprise-ai-backend"
