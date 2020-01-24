"""Helper functions for selected tests API."""
from typing import List

from evergreen import EvergreenApi, Project
from fastapi import HTTPException

from selectedtests.evergreen_helper import get_evg_project


def try_retrieve_evergreen_project(project: str, api: EvergreenApi) -> Project:
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


def parse_changed_files(changed_files: str) -> List[str]:
    """
    Get the list of strings specified in CSV format under change_files query parameter.

    :param changed_files: The CSV string.
    :return: The parsed list of strings.
    """
    return changed_files.split(",")
