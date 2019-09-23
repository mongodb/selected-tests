import pytest
import app


@pytest.fixture()
def app_client():
    """
    Client for the flask web with mocked endpoints.
    """
    client = app.create_app().test_client()
    return client


def test_health(app_client):
    """
    Test /health endpoint
    """
    response = app_client.get('/health', follow_redirects=True)
    assert response.status_code == 200
