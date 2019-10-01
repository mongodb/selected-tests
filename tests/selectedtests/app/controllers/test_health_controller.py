from flask import testing


def test_health_endpoint(app_client: testing.FlaskClient):
    """
    Test /health endpoint
    """
    response = app_client.get("/health")
    assert response.status_code == 200
    res_data = response.get_data(as_text=True)
    assert "online" in res_data and "true" in res_data
