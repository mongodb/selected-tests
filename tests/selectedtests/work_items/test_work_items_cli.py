from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import pytz

from click.testing import CliRunner

import selectedtests.work_items.work_items_cli as under_test

NS = "selectedtests.work_items.work_items_cli"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestGetAfterDate:
    def test_compare_to_timezone_aware_date(self):
        after_date = under_test._get_after_date(0)
        timezome_aware_date = datetime(2014, 12, 10, 12, 0, 0, tzinfo=pytz.utc)
        assert after_date > timezome_aware_date

    def test_raises_error_when_compared_against_non_offset_aware_date(self):
        after_date = under_test._get_after_date(0)
        comparison_date = datetime.utcnow()
        with pytest.raises(TypeError):
            after_date < comparison_date


class TestCli:
    @patch(ns("get_evg_api"))
    @patch(ns("MongoWrapper.connect"))
    @patch(ns("process_queued_test_mapping_work_items"))
    def test_process_test_mappings(
        self, process_queued_test_mapping_work_items_mock, mongo_wrapper_mock, evg_api_mock
    ):
        evg_api_mock.get_api.return_value = MagicMock()
        mongo_wrapper_mock.get_api.return_value = MagicMock()
        process_queued_test_mapping_work_items_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                under_test.cli, ["--mongo-uri=localhost", "process-test-mappings"]
            )
            assert result.exit_code == 0

    @patch(ns("get_evg_api"))
    @patch(ns("MongoWrapper.connect"))
    @patch(ns("process_queued_task_mapping_work_items"))
    def test_process_task_mappings(
        self, process_queued_task_mapping_work_items_mock, mongo_wrapper_mock, evg_api_mock
    ):
        evg_api_mock.get_api.return_value = MagicMock()
        mongo_wrapper_mock.get_api.return_value = MagicMock()
        process_queued_task_mapping_work_items_mock.return_value = "mock-response"

        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                under_test.cli, ["--mongo-uri=localhost", "process-task-mappings"]
            )
            assert result.exit_code == 0
