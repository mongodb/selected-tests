from starlette.testclient import TestClient


def test_health_endpoint(app_client: TestClient):
    response = app_client.get("/health")
    assert response.status_code == 200
    response_data = response.json()
    assert "online" in response_data and response_data["online"]
