import pytest

from selectedtests.app import app


@pytest.fixture()
def app_client():
    """
    Client for the flask web with mocked endpoints.
    """
    client = app.create_app().test_client()
    return client
