import json

from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from selectedtests.task_mappings.cli import cli

NS = "selectedtests.task_mappings.cli"
MAPPINGS_NS = "selectedtests.task_mappings.mappings"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


def m_ns(relative_name):
    """Return a full name to mappings from a name relative to the tested module"s name space."""
    return MAPPINGS_NS + "." + relative_name


class TestCli:
    @patch(m_ns("init_repo"))
    @patch(ns("RetryingEvergreenApi"))
    @patch(m_ns("_get_filtered_files"))
    def test_integration(
        self,
        filtered_files_mock,
        evg_api,
        init_repo_mock,
        evg_versions,
        expected_task_mappings_output,
    ):
        mock_evg_api = MagicMock()
        mock_evg_api.versions_by_project.return_value = evg_versions
        evg_api.get_api.return_value = mock_evg_api

        project_name = "mongodb-mongo-master"
        mock_evg_api.all_projects.return_value = [
            MagicMock(identifier=project_name),
            MagicMock(identifier="fake_name"),
        ]

        filtered_files_mock.return_value = ["src/file1", "src/file2"]

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    project_name,
                    "--source-file-regex",
                    "src.*",
                    "--output-file",
                    output_file,
                    "--start",
                    "2019-10-11T19:10:38",
                    "--end",
                    "2019-10-11T19:30:38",
                ],
            )
            assert result.exit_code == 0
            with open(output_file, "r") as data:
                output = json.load(data)
                assert expected_task_mappings_output == output

    @patch(ns("RetryingEvergreenApi"))
    @patch(ns("TaskMappings.create_task_mappings"))
    def test_arguments_passed_in(self, create_task_mappings_mock, evg_api):
        mock_evg_api = MagicMock()
        evg_api.get_api.return_value = mock_evg_api
        expected_result = {"result": "mock-response"}
        created_task_mock = MagicMock()
        created_task_mock.transform.return_value = expected_result
        create_task_mappings_mock.return_value = created_task_mock

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--module-name",
                    "my-module",
                    "--source-file-regex",
                    ".*",
                    "--module-source-file-regex",
                    ".*",
                    "--output-file",
                    output_file,
                    "--start",
                    "2019-10-11T19:10:38",
                    "--end",
                    "2019-10-11T19:30:38",
                ],
            )
            assert result.exit_code == 0
            with open(output_file, "r") as data:
                output = json.load(data)
                assert expected_result == output

    @patch(ns("RetryingEvergreenApi"))
    @patch(ns("TaskMappings.create_task_mappings"))
    def test_invalid_dates(self, create_task_mappings_mock, evg_api):
        mock_evg_api = MagicMock()
        evg_api.get_api.return_value = mock_evg_api
        create_task_mappings_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--module-name",
                    "my-module",
                    "--source-file-regex",
                    ".*",
                    "--module-source-file-regex",
                    ".*",
                    "--output-file",
                    output_file,
                    "--start",
                    "2019",
                    "--end",
                    "2019",
                ],
            )
            assert result.exit_code == 1
            assert (
                "The start or end date could not be parsed - make sure it's an iso date"
                in result.stdout
            )

    @patch(ns("RetryingEvergreenApi"))
    @patch(ns("TaskMappings.create_task_mappings"))
    def test_module_regexes_not_passed_in(self, create_task_mappings_mock, evg_api):
        mock_evg_api = MagicMock()
        evg_api.get_api.return_value = mock_evg_api
        create_task_mappings_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--module-name",
                    "my-module",
                    "--source-file-regex",
                    ".*",
                    "--output-file",
                    output_file,
                    "--start",
                    "2019-10-11T19:10:38",
                    "--end",
                    "2019-10-11T19:30:38",
                ],
            )
            assert result.exit_code == 1
            assert (
                "A module source file regex is required when a module is being analyzed"
                in result.stdout
            )
