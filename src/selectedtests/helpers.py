"""Helper functions for Cli entry points."""
import os
import structlog
import logging

from evergreen.api import RetryingEvergreenApi
from evergreen.config import EvgAuth
from selectedtests.datasource.mongo_wrapper import MongoWrapper


def get_evg_api():
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
    return MongoWrapper.connect(mongo_uri)


def setup_logging(verbose: bool):
    """Set up logging configuration."""
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)
