"""Evergreen.py helper."""
from typing import Dict
from evergreen.api import EvergreenApi


def get_evg_project(evg_api: EvergreenApi, project: str) -> Dict:
    """
    Fetch an Evergreen project's info from the Evergreen API.

    :param evg_api: An instance of the evg_api client
    :param project: The name of the evergreen project to analyze.
    :return: evg_api client instance of the project
    """
    for evergreen_project in evg_api.all_projects():
        if evergreen_project.identifier == project:
            return evergreen_project
    return None
