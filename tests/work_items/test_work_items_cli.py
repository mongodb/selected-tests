from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from selectedtests.work_items.cli import cli

NS = "selectedtests.work_items.cli"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestCli:
    @patch(ns("RetryingEvergreenApi"))
    @patch(ns("MongoWrapper"))
    @patch(ns("process_queued_work_items"))
    def test_arguments_passed_in(
        self, process_queued_work_items_mock, mongo_wrapper_mock, evg_api_mock
    ):
        evg_api_mock.get_api.return_value = MagicMock()
        mongo_wrapper_mock.get_api.return_value = MagicMock()
        process_queued_work_items_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["process-test-mappings"])
            assert result.exit_code == 0
