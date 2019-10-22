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
    @patch(ns("CachedEvergreenApi"))
    @patch(m_ns("_get_filtered_files"))
    def test_integration(
        self, filtered_files_mock, cached_evg_api, evg_versions, expected_task_mappings_output
    ):
        mock_evg_api = MagicMock()
        mock_evg_api.versions_by_project.return_value = evg_versions
        cached_evg_api.get_api.return_value = mock_evg_api

        filtered_files_mock.return_value = ["src/file1", "src/file2"]

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "create",
                    "mongodb-mongo-master",
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
