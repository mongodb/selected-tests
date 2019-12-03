from flask import testing


def test_health_endpoint(app_client: testing.FlaskClient):
    """
    Test /health endpoint
    """
    response = app_client.get("/health")
    assert response.status_code == 200
    response_data = response.get_json()
    assert "online" in response_data and response_data["online"]
