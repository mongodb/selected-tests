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