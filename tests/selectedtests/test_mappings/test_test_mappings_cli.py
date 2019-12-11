import json

from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from selectedtests.test_mappings.test_mappings_cli import cli

NS = "selectedtests.test_mappings.test_mappings_cli"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestCli:
    @patch(ns("get_evg_api"))
    @patch(ns("generate_test_mappings"))
    def test_arguments_passed_in(self, generate_test_mappings_mock, get_evg_api_mock):
        mock_evg_api = MagicMock()
        get_evg_api_mock.return_value = mock_evg_api
        generate_test_mappings_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--after-project-commit",
                    "SHA1",
                    "--source-file-regex",
                    ".*",
                    "--test-file-regex",
                    ".*",
                    "--module-name",
                    "my-module",
                    "--after-module-commit",
                    "SHA2",
                    "--module-source-file-regex",
                    ".*",
                    "--module-test-file-regex",
                    ".*",
                    "--output-file",
                    output_file,
                ],
            )
            assert result.exit_code == 0
            with open(output_file, "r") as data:
                output = json.load(data)
                assert output == "mock-response"

    @patch(ns("get_evg_api"))
    @patch(ns("generate_test_mappings"))
    def test_module_after_commit_sha_not_passed_in(
        self, generate_test_mappings_mock, get_evg_api_mock
    ):
        mock_evg_api = MagicMock()
        get_evg_api_mock.return_value = mock_evg_api
        generate_test_mappings_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--after-project-commit",
                    "SHA1",
                    "--source-file-regex",
                    ".*",
                    "--test-file-regex",
                    ".*",
                    "--module-name",
                    "my-module",
                    "--output-file",
                    output_file,
                ],
            )
            assert result.exit_code == 1
            assert (
                "A module after-commit value is required when a module is being analyzed"
                in result.stdout
            )

    @patch(ns("get_evg_api"))
    @patch(ns("generate_test_mappings"))
    def test_module_regexes_not_passed_in(self, generate_test_mappings_mock, get_evg_api_mock):
        mock_evg_api = MagicMock()
        get_evg_api_mock.return_value = mock_evg_api
        generate_test_mappings_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--after-project-commit",
                    "SHA1",
                    "--source-file-regex",
                    ".*",
                    "--test-file-regex",
                    ".*",
                    "--module-name",
                    "my-module",
                    "--after-module-commit",
                    "SHA2",
                    "--output-file",
                    output_file,
                ],
            )
            assert result.exit_code == 1
            assert (
                "A module source file regex is required when a module is being analyzed"
                in result.stdout
            )
