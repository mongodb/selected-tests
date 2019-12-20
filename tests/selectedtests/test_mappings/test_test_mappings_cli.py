import json

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from selectedtests.test_mappings.create_test_mappings import TestMappingsResult
from selectedtests.test_mappings.test_mappings_cli import cli

NS = "selectedtests.test_mappings.test_mappings_cli"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestCli:
    @patch(ns("get_evg_api"))
    @patch(ns("generate_test_mappings"))
    def test_create_with_arguments_passed_in(self, generate_test_mappings_mock, get_evg_api_mock):
        mock_evg_api = MagicMock()
        get_evg_api_mock.return_value = mock_evg_api
        generate_test_mappings_mock.return_value = TestMappingsResult(
            test_mappings_list=["mock-mapping"],
            most_recent_project_commit_analyzed="last-project-sha-analyzed",
            most_recent_module_commit_analyzed="last-module-sha-analyzed",
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--source-file-regex",
                    ".*",
                    "--test-file-regex",
                    ".*",
                    "--module-name",
                    "my-module",
                    "--module-source-file-regex",
                    ".*",
                    "--module-test-file-regex",
                    ".*",
                    "--after",
                    "2019-10-11T19:10:38",
                    "--output-file",
                    output_file,
                ],
            )
            assert result.exit_code == 0
            with open(output_file, "r") as data:
                output = json.load(data)
                assert output == ["mock-mapping"]

    @patch(ns("get_evg_api"))
    @patch(ns("generate_test_mappings"))
    def test_create_with_invalid_dates(self, generate_test_mappings_mock, get_evg_api_mock):
        mock_evg_api = MagicMock()
        get_evg_api_mock.return_value = mock_evg_api
        generate_test_mappings_mock.return_value = TestMappingsResult(
            test_mappings_list=["mock-mapping"],
            most_recent_project_commit_analyzed="last-project-sha-analyzed",
            most_recent_module_commit_analyzed="last-module-sha-analyzed",
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--source-file-regex",
                    ".*",
                    "--test-file-regex",
                    ".*",
                    "--module-name",
                    "my-module",
                    "--after",
                    "2019",
                    "--output-file",
                    output_file,
                ],
            )
            assert result.exit_code == 1
            assert (
                "The after date could not be parsed - make sure it's an iso date" in result.stdout
            )

    @patch(ns("get_evg_api"))
    @patch(ns("generate_test_mappings"))
    def test_create_with_module_regexes_not_passed_in(
        self, generate_test_mappings_mock, get_evg_api_mock
    ):
        mock_evg_api = MagicMock()
        get_evg_api_mock.return_value = mock_evg_api
        generate_test_mappings_mock.return_value = TestMappingsResult(
            test_mappings_list=["mock-mapping"],
            most_recent_project_commit_analyzed="last-project-sha-analyzed",
            most_recent_module_commit_analyzed="last-module-sha-analyzed",
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
                    "--source-file-regex",
                    ".*",
                    "--test-file-regex",
                    ".*",
                    "--module-name",
                    "my-module",
                    "--after",
                    "2019-10-11T19:10:38",
                    "--output-file",
                    output_file,
                ],
            )
            assert result.exit_code == 1
            assert (
                "A module source file regex is required when a module is being analyzed"
                in result.stdout
            )

    @patch(ns("get_evg_api"))
    @patch(ns("MongoWrapper.connect"))
    @patch(ns("update_test_mappings_since_last_commit"))
    def test_update(
        self, update_test_mappings_since_last_commit_mock, mongo_wrapper_mock, evg_api_mock
    ):
        evg_api_mock.get_api.return_value = MagicMock()
        mongo_wrapper_mock.get_api.return_value = MagicMock()

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["update", "--mongo-uri=localhost"])
            assert result.exit_code == 0
