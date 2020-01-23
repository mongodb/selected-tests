"""Parsers used in selected tests API."""
from typing import List

from evergreen import EvergreenApi, Project
from fastapi import Depends, HTTPException
from starlette.requests import Request

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.evergreen_helper import get_evg_project


def changed_files_parser(changed_files: str) -> List[str]:
    """
    Get the list of strings specified in CSV format under change_files query parameter.

    :param changed_files: The CSV string.
    :return: The parsed list of strings.
    """
    return changed_files.split(",")


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


def retrieve_evergreen_project(project: str, api: EvergreenApi = Depends(get_evg)) -> Project:
    """
    Get the Evergreen project for a request by project id.

    :param project: The project id.
    :param api: The Evergreen API client.
    :return: The project.
    """
    evergreen_project = get_evg_project(api, project)
    if not evergreen_project:
        raise HTTPException(status_code=404, detail="Evergreen project not found")
    return evergreen_project
