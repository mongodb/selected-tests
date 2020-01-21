"""Helper functions for Cli entry points."""
import os

from evergreen.api import EvergreenApi, RetryingEvergreenApi
from evergreen.config import EvgAuth

from selectedtests.datasource.mongo_wrapper import MongoWrapper


def get_evg_api() -> EvergreenApi:
    """
    Create an instance of the evergreen API based on environment variables.

    :return: Evergreen API instance.
    """
    evg_user = os.environ.get("EVG_API_USER")
    evg_api_key = os.environ.get("EVG_API_KEY")
    return RetryingEvergreenApi.get_api(auth=EvgAuth(evg_user, evg_api_key))


def get_mongo_wrapper() -> MongoWrapper:
    """
    Get an instance of the mongo wrapper based on environment variables.

    :return: MongoWrapper instance.
    """
    mongo_uri = os.environ.get("SELECTED_TESTS_MONGO_URI")
    if mongo_uri is None:
        raise RuntimeError("Cannot connect to mongodb, SELECTED_TESTS_MONGO_URI is not set")
    return MongoWrapper.connect(mongo_uri)
