from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from selectedtests.work_items.cli import cli

NS = "selectedtests.work_items.cli"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestCli:
    @patch(ns("get_evg_api"))
    @patch(ns("get_mongo_wrapper"))
    @patch(ns("process_queued_test_mapping_work_items"))
    def test_process_test_mappings(
        self, process_queued_test_mapping_work_items_mock, mongo_wrapper_mock, evg_api_mock
    ):
        evg_api_mock.get_api.return_value = MagicMock()
        mongo_wrapper_mock.get_api.return_value = MagicMock()
        process_queued_test_mapping_work_items_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["process-test-mappings"])
            assert result.exit_code == 0

    @patch(ns("get_evg_api"))
    @patch(ns("get_mongo_wrapper"))
    @patch(ns("process_queued_task_mapping_work_items"))
    def test_process_task_mappings(
        self, process_queued_task_mapping_work_items_mock, mongo_wrapper_mock, evg_api_mock
    ):
        evg_api_mock.get_api.return_value = MagicMock()
        mongo_wrapper_mock.get_api.return_value = MagicMock()
        process_queued_task_mapping_work_items_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["process-task-mappings"])
            assert result.exit_code == 0
