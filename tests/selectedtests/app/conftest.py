from unittest.mock import MagicMock

import pytest

from selectedtests.app import app


@pytest.fixture()
def app_client():
    """
    Client for the flask web with mocked endpoints.
    """
    mongo = MagicMock()
    evg_api = MagicMock()
    client = app.create_app(mongo, evg_api).test_client()
    return client
