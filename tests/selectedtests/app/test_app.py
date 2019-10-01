from flask import testing


def test_swagger_endpoint(app_client: testing.FlaskClient):
    """
    Test /health endpoint
    """
    response = app_client.get("/swagger")
    assert response.status_code == 200


def test_swagger_json_endpoint(app_client: testing.FlaskClient):
    """
    Test /health endpoint
    """
    response = app_client.get("/swagger.json")
    assert response.status_code == 200
