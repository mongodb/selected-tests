import pytest

from selectedtests import app as under_test


@pytest.fixture()
def app_client():
    """
    Client for the flask web with mocked endpoints.
    """
    client = under_test.create_app().test_client()
    return client


def test_health(app_client):
    """
    Test /health endpoint
    """
    response = app_client.get('/health')
    assert response.status_code == 200
    assert "ok" in response.get_data(as_text=True)
