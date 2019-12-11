"""Evergreen.py helper."""
from typing import Optional

from evergreen.api import EvergreenApi, Project
from evergreen.manifest import ManifestModule


def get_evg_project(evg_api: EvergreenApi, project: str) -> Optional[Project]:
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


def get_evg_module_for_project(
    evg_api: EvergreenApi, project: str, module_repo: str
) -> ManifestModule:
    """
    Fetch the module associated with an Evergreen project.

    :param evg_api: An instance of the evg_api client
    :param project: The name of the evergreen project to analyze
    :param module_repo: Name of the module to analyze
    :return: evg_api client instance of the module
    """
    version_iterator = evg_api.versions_by_project(project)
    recent_version = next(version_iterator)
    modules = recent_version.get_manifest().modules
    return modules.get(module_repo)
