"""Evergreen.py helper."""
from datetime import datetime
from typing import Optional

from evergreen.api import EvergreenApi, Project
from evergreen.manifest import ManifestModule
from tempfile import TemporaryDirectory

from selectedtests.git_helper import init_repo


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


def get_project_commit_on_date(
    temp_dir: TemporaryDirectory, evg_api: EvergreenApi, project: str, after_date: datetime
):
    """
    Fetch the earliest commit in an Evergreen project's repo that comes after a given after_date.

    :param temp_dir: The place where to clone the repo to
    :param evg_api: An instance of the evg_api client
    :param project: The name of the evergreen project to analyze
    :param after_date: The date after which the desired commit should occur
    :return: The commit sha of the desired project repo commit
    """
    evg_project = get_evg_project(evg_api, project)
    project_repo = init_repo(
        temp_dir, evg_project.repo_name, evg_project.branch_name, evg_project.owner_name
    )
    project_commit = None

    for commit in project_repo.iter_commits(project_repo.head.commit):
        if commit.committed_datetime < after_date:
            break
        project_commit = commit.hexsha

    return project_commit


def get_module_commit_on_date(
    temp_dir: TemporaryDirectory,
    evg_api: EvergreenApi,
    project: str,
    module_name: str,
    after_date: datetime,
):
    """
    Fetch the earliest commit in an Evergreen module's repo that comes after a given after_date.

    :param temp_dir: The place where to clone the repo to
    :param evg_api: An instance of the evg_api client
    :param project: The name of the evergreen project to analyze
    :param module_name: The name of the Evergreen module to analyze
    :param after_date: The date after which the desired commit should occur
    :return: The commit sha of the desired module repo commit
    """
    module = get_evg_module_for_project(evg_api, project, module_name)
    module_repo = init_repo(temp_dir, module.repo, module.branch, module.owner)
    module_commit = None

    for commit in module_repo.iter_commits(module_repo.head.commit):
        if commit.committed_datetime < after_date:
            break
        module_commit = commit.hexsha

    return module_commit


def get_version_on_date(evg_api: EvergreenApi, project: str, after_date: datetime):
    """
    Fetch the earliest Evergreen version that comes after a given after_date.

    :param evg_api: An instance of the evg_api client
    :param project: The name of the evergreen project to analyze
    :param after_date: The date after which the desired commit should occur
    :return: The version_id of the desired version
    """
    project_versions = evg_api.versions_by_project_time_window(
        project, datetime.utcnow(), after_date
    )
    after_version = None
    for version in project_versions:
        after_version = version.version_id
    return after_version
