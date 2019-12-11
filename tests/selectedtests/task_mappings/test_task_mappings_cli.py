import json

from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from selectedtests.task_mappings.task_mappings_cli import cli

NS = "selectedtests.task_mappings.task_mappings_cli"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestCli:
    @patch(ns("get_evg_api"))
    @patch(ns("TaskMappings.create_task_mappings"))
    def test_arguments_passed_in(self, create_task_mappings_mock, get_evg_api_mock):
        mock_get_evg_api_mock = MagicMock()
        get_evg_api_mock.return_value = mock_get_evg_api_mock
        expected_result = ["mock-response"]
        created_task_mock = MagicMock()
        created_task_mock.transform.return_value = expected_result
        create_task_mappings_mock.return_value = (created_task_mock, "most-recent-sha-analyzed")

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
                    "--after-version",
                    "version-sha",
                ],
            )
            assert result.exit_code == 0
            with open(output_file, "r") as data:
                output = json.load(data)
                assert expected_result == output

    @patch(ns("get_evg_api"))
    @patch(ns("TaskMappings.create_task_mappings"))
    def test_module_regexes_not_passed_in(self, create_task_mappings_mock, get_evg_api_mock):
        mock_get_evg_api_mock = MagicMock()
        get_evg_api_mock.return_value = mock_get_evg_api_mock
        create_task_mappings_mock.return_value = ("mock-response", "most-recent-sha-analyzed")

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
                    "--after-version",
                    "version-sha",
                ],
            )
            assert result.exit_code == 1
            assert (
                "A module source file regex is required when a module is being analyzed"
                in result.stdout
            )
