from flask import testing


def test_health_endpoint(app_client: testing.FlaskClient):
    """
    Test /health endpoint
    """
    response = app_client.get("/health")
    assert response.status_code == 200
    assert "online" and "true" in response.get_data(as_text=True)
