import pytest
import os
import json
from unittest.mock import MagicMock
from typing import List, Dict
from datetime import datetime

TASKS_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
SAMPLE_OUTPUT_PATH = os.path.join(TASKS_DIRECTORY, "sample_data")
SAMPLE_VERSIONS_PATH = os.path.join(TASKS_DIRECTORY, "sample_data", "sample_versions")
VERSIONS = ["next_version", "current_version", "prev_version"]


@pytest.fixture()
def expected_output():
    with open(os.path.join(SAMPLE_OUTPUT_PATH, "expected.json"), "r") as data:
        return json.load(data)


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
