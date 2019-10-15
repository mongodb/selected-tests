import json
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from selectedtests.cli import cli

NS = "selectedtests.cli"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestCli:
    @patch(ns("CachedEvergreenApi"))
    def test_integration(self, cached_evg_api, evg_versions, expected_output):
        mock_evg_api = MagicMock()
        mock_evg_api.versions_by_project.return_value = evg_versions
        cached_evg_api.get_api.return_value = mock_evg_api

        runner = CliRunner()
        with runner.isolated_filesystem():
            output_file = "output.txt"
            result = runner.invoke(
                cli,
                [
                    "task",
                    "mongodb-mongo-master",
                    "--file-regex",
                    "src.*",
                    "--output-file",
                    output_file,
                ],
            )
            assert result.exit_code == 0
            with open(output_file, "r") as data:
                output = json.load(data)
                assert expected_output == output
