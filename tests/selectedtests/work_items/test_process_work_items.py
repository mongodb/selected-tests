import selectedtests.work_items.process_work_items as under_test
from unittest.mock import MagicMock, patch


NS = "selectedtests.work_items.process_work_items"


def ns(relative_name):  # pylint: disable=invalid-name
    """Return a full name from a name relative to the test module"s name space."""
    return NS + "." + relative_name


class TestSetupIndexes:
    def test_indexes_created(self):
        collection = MagicMock()

        under_test.setup_indexes(collection)

        collection.create_indexes.assert_called_once()


class TestProcessQueuedWorkItems:
    @patch(ns("_process_one_work_item"))
    def test_analyze_runs_while_work_available(self, mock_process_one_work_item):
        n_work_items = 3
        mock_process_one_work_item.side_effect = [False] * n_work_items + [True]
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test.process_queued_work_items(evg_api_mock, mongo_mock, None, None)

        assert n_work_items + 1 == mock_process_one_work_item.call_count

    @patch(ns("_process_one_work_item"))
    def test_analyze_does_not_throw_exceptions(self, mock_process_one_work_item):
        mock_process_one_work_item.side_effect = ValueError("Unexpected Exception")
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test.process_queued_work_items(evg_api_mock, mongo_mock, None, None)


class TestProcessOneWorkItem:
    @patch(ns("ProjectTestMappingWorkItem"))
    def test_returns_true_if_no_work(self, work_item_mock):
        work_item_mock.next.return_value = None
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        work_done = under_test._process_one_work_item(evg_api_mock, mongo_mock, None, None)

        assert work_done

    @patch(ns("ProjectTestMappingWorkItem"))
    @patch(ns("_run_create_test_mappings"))
    def test_work_items_completed_successfully__are_marked_complete(
        self, run_create_test_mappings_mock, work_item_mock
    ):
        work_item_mock.next.return_value = MagicMock()
        run_create_test_mappings_mock.return_value = True
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        work_done = under_test._process_one_work_item(evg_api_mock, mongo_mock, None, None)

        work_item_mock.next.return_value.complete.assert_called_once()
        assert not work_done

    @patch(ns("ProjectTestMappingWorkItem"))
    @patch(ns("_run_create_test_mappings"))
    def test_work_items_completed_unsuccessfully_are_marked_not_complete(
        self, run_create_test_mappings_mock, work_item_mock
    ):
        work_item_mock.next.return_value = MagicMock()
        run_create_test_mappings_mock.return_value = False
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        work_done = under_test._process_one_work_item(evg_api_mock, mongo_mock, None, None)

        work_item_mock.next.return_value.complete.assert_not_called()
        assert not work_done


class TestRunCreateTaskMappings:
    @patch(ns("generate_test_mappings"))
    def test_mappings_are_created(self, generate_test_mappings_mock):
        generate_test_mappings_mock.return_value = ["mock-mapping"]
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        logger_mock = MagicMock()
        work_item_mock = MagicMock(source_file_regex="src", test_file_regex="test", module=None)

        under_test._run_create_test_mappings(
            evg_api_mock, mongo_mock, work_item_mock, None, None, logger_mock
        )

        mongo_mock.test_mappings.return_value.insert_many.assert_called_once_with(["mock-mapping"])

    @patch(ns("generate_test_mappings"))
    def test_no_mappings_are_created(self, generate_test_mappings_mock):
        generate_test_mappings_mock.return_value = []
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        logger_mock = MagicMock()
        mongo_mock.test_mappings.return_value.insert_many.side_effect = TypeError(
            "documents must be a non-empty list"
        )
        work_item_mock = MagicMock(source_file_regex="src", test_file_regex="test", module=None)

        under_test._run_create_test_mappings(
            evg_api_mock, mongo_mock, work_item_mock, None, None, logger_mock
        )

        mongo_mock.test_mappings.return_value.insert_many.assert_not_called()
