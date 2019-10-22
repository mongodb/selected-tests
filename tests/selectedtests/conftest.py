import git
import json
import os
import pytest

from unittest.mock import MagicMock
from typing import List, Dict
from datetime import datetime, time, timedelta

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
SAMPLE_OUTPUT_PATH = os.path.join(CURRENT_DIRECTORY, "sample_data")
SAMPLE_VERSIONS_PATH = os.path.join(CURRENT_DIRECTORY, "sample_data", "sample_versions")
VERSIONS = ["next_version", "current_version", "prev_version"]


@pytest.fixture()
def expected_task_mappings_output():
    with open(os.path.join(SAMPLE_OUTPUT_PATH, "expected_task_mappings.json"), "r") as data:
        return json.load(data)


@pytest.fixture()
def expected_test_mappings_output():
    with open(os.path.join(SAMPLE_OUTPUT_PATH, "expected_test_mappings.json"), "r") as data:
        return json.load(data)


@pytest.fixture()
def evg_projects() -> List[MagicMock]:
    return [
        MagicMock(
            repo_name="my-repo-1",
            branch_name="master",
            owner_name="10gen",
            identifier="mongodb-manual",
        ),
        MagicMock(
            repo_name="my-repo-2",
            branch_name="master",
            owner_name="10gen",
            identifier="mongodb-mongo-master",
        ),
    ]


@pytest.fixture()
def evg_versions() -> List[MagicMock]:
    versions = []
    for version in VERSIONS:
        with open(os.path.join(SAMPLE_VERSIONS_PATH, f"{version}.json"), "r") as data:
            versions.append(_create_version_mocks(json.load(data)))

    return versions


def _create_version_mocks(data: Dict) -> MagicMock:
    version_mock = MagicMock(
        branch=data.get("branch"),
        create_time=datetime.fromisoformat(data.get("create_time")),
        start_time=datetime.fromisoformat(data.get("start_time")),
        project=data.get("project"),
        repo=data.get("repo"),
        revision=data.get("revision"),
        version_id=data.get("version_id"),
    )

    builds = data.get("builds")
    version_mock.mock_builds = _create_build_mocks(builds)
    version_mock.get_builds.return_value = version_mock.mock_builds

    def get_build_by_variant(variant: str):
        for build in version_mock.mock_builds:
            if build.build_variant == variant:
                return build

    version_mock.build_by_variant.side_effect = get_build_by_variant

    manifest = MagicMock(modules={})

    version_mock.get_manifest.return_value = manifest

    return version_mock


def _create_build_mocks(builds: Dict) -> List:
    build_mocks = []
    for variant in builds:
        build = builds.get(variant)
        build_mock = MagicMock(
            display_name=build.get("display_name"),
            build_variant=build.get("build_variant"),
            tasks=_create_task_mocks(build.get("tasks")),
        )
        build_mock.get_tasks.return_value = build_mock.tasks
        build_mocks.append(build_mock)

    return build_mocks


def _create_task_mocks(tasks: List) -> List:
    task_mocks = []
    for task in tasks:
        task_mock = MagicMock(
            display_name=task.get("display_name"),
            activated=task.get("activated"),
            status=task.get("status"),
        )
        task_mocks.append(task_mock)
    return task_mocks


def initialize_temp_repo(directory):
    repo = git.Repo.init(directory)
    repo.index.commit("initial commit -- no files changed")
    return repo


@pytest.fixture(scope="module")
def repo_with_no_source_files_changed():
    def _repo(temp_directory):
        repo = initialize_temp_repo(temp_directory)
        return repo

    return _repo


@pytest.fixture(scope="module")
def repo_with_one_source_file_and_no_test_files_changed():
    def _repo(temp_directory):
        repo = initialize_temp_repo(temp_directory)
        source_file = os.path.join(temp_directory, "new-source-file")
        open(source_file, "wb").close()
        repo.index.add([source_file])
        repo.index.commit("add source file")
        return repo

    return _repo


@pytest.fixture(scope="module")
def repo_with_no_source_files_and_one_test_file_changed():
    def _repo(temp_directory):
        repo = initialize_temp_repo(temp_directory)
        test_file = os.path.join(temp_directory, "new-test-file")
        open(test_file, "wb").close()
        repo.index.add([test_file])
        repo.index.commit("add test file")
        return repo

    return _repo


@pytest.fixture(scope="module")
def repo_with_one_source_file_and_one_test_file_changed_in_same_commit():
    def _repo(temp_directory):
        repo = initialize_temp_repo(temp_directory)
        source_file = os.path.join(temp_directory, "new-source-file")
        test_file = os.path.join(temp_directory, "new-test-file")
        open(source_file, "wb").close()
        open(test_file, "wb").close()
        repo.index.add([source_file, test_file])
        repo.index.commit("add source and test file in same commit")
        return repo

    return _repo


@pytest.fixture(scope="module")
def repo_with_one_source_file_and_one_test_file_changed_in_different_commits():
    def _repo(temp_directory):
        repo = initialize_temp_repo(temp_directory)
        source_file = os.path.join(temp_directory, "new-source-file")
        open(source_file, "wb").close()
        repo.index.add([source_file])
        repo.index.commit("add source file")
        test_file = os.path.join(temp_directory, "new-test-file")
        open(test_file, "wb").close()
        repo.index.add([test_file])
        repo.index.commit("add test file")
        return repo

    return _repo


@pytest.fixture(scope="module")
def repo_with_files_added_two_days_ago():
    def _repo(temp_directory):
        two_days_ago = str(datetime.combine(datetime.now() - timedelta(days=2), time()))
        os.environ["GIT_AUTHOR_DATE"] = two_days_ago
        os.environ["GIT_COMMITTER_DATE"] = two_days_ago

        repo = initialize_temp_repo(temp_directory)
        source_file = os.path.join(temp_directory, "new-source-file")
        test_file = os.path.join(temp_directory, "new-test-file")
        open(source_file, "wb").close()
        open(test_file, "wb").close()
        repo.index.add([source_file, test_file])
        repo.index.commit("add source and test file in same commit 2 days ago")
        return repo

    return _repo
