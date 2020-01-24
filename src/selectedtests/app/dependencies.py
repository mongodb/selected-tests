"""Parsers used in selected tests API."""

from evergreen import EvergreenApi
from starlette.requests import Request

from selectedtests.datasource.mongo_wrapper import MongoWrapper


def get_db(request: Request) -> MongoWrapper:
    """
    Get the configured database for the application.

    :param request: The request needing access to the database.
    :return: The database.
    """
    return request.app.state.db


def get_evg(request: Request) -> EvergreenApi:
    """
    Get the configured Evergreen API client for the application.

    :param request: The request needing the Evergreen API client.
    :return: The Evergreen API client.
    """
    return request.app.state.evg_api
