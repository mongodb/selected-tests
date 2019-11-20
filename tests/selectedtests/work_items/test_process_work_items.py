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


class TestProcessQueuedTaskMappingWorkItems:
    @patch(ns("_process_one_task_mapping_work_item"))
    @patch(ns("_generate_task_mapping_work_items"))
    def test_analyze_runs_while_work_available(
        self, mock_gen_task_map_work_items, mock_process_one_task_mapping_work_item
    ):
        n_work_items = 3
        mock_gen_task_map_work_items.return_value = [MagicMock() for _ in range(n_work_items)]
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test.process_queued_task_mapping_work_items(evg_api_mock, mongo_mock, None, None)

        assert n_work_items == mock_process_one_task_mapping_work_item.call_count

    @patch(ns("_process_one_task_mapping_work_item"))
    def test_analyze_does_not_throw_exceptions(self, mock_process_one_task_mapping_work_item):
        mock_process_one_task_mapping_work_item.side_effect = ValueError("Unexpected Exception")
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test.process_queued_task_mapping_work_items(evg_api_mock, mongo_mock, None, None)


class TestGenerateTaskMappingWorkItems:
    @patch(ns("ProjectTaskMappingWorkItem.next"))
    def test_no_work_items_available(self, next_mock):
        mongo_mock = MagicMock()
        next_mock.return_value = None

        found_items = [item for item in under_test._generate_task_mapping_work_items(mongo_mock)]

        assert 0 == len(found_items)

    @patch(ns("ProjectTaskMappingWorkItem.next"))
    def test_items_generated_until_exhausted(self, next_mock):
        mongo_mock = MagicMock()
        n_items = 5
        next_mock.side_effect = [MagicMock() for _ in range(n_items)] + [None]

        found_items = [item for item in under_test._generate_task_mapping_work_items(mongo_mock)]

        assert n_items == len(found_items)


class TestProcessOneTaskMappingWorkItem:
    @patch(ns("_run_create_task_mappings"))
    def test_work_items_completed_successfully_are_marked_complete(
        self, run_create_task_mappings_mock
    ):
        work_item_mock = MagicMock()
        run_create_task_mappings_mock.return_value = True
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test._process_one_task_mapping_work_item(
            work_item_mock, evg_api_mock, mongo_mock, None, None
        )

        work_item_mock.complete.assert_called_once()

    @patch(ns("_run_create_task_mappings"))
    def test_work_items_completed_unsuccessfully_are_marked_not_complete(
        self, run_create_task_mappings_mock
    ):
        work_item_mock = MagicMock()
        run_create_task_mappings_mock.return_value = False
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test._process_one_task_mapping_work_item(
            work_item_mock, evg_api_mock, mongo_mock, None, None
        )

        work_item_mock.next.return_value.complete.assert_not_called()


class TestRunCreateTaskMappings:
    @patch(ns("TaskMappings.create_task_mappings"))
    def test_task_mappings_are_created(self, create_task_mappings_mock):
        task_mappings_mock = MagicMock()
        task_mappings_mock.transform.return_value = ["mock-response"]
        create_task_mappings_mock.return_value = task_mappings_mock
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        logger_mock = MagicMock()
        work_item_mock = MagicMock(source_file_regex="src", module=None)

        under_test._run_create_task_mappings(
            evg_api_mock, mongo_mock, work_item_mock, None, None, logger_mock
        )

        mongo_mock.task_mappings.return_value.insert_many.assert_called_once_with(["mock-response"])

    @patch(ns("TaskMappings.create_task_mappings"))
    def test_no_mappings_are_created(self, create_task_mappings_mock):
        task_mappings_mock = MagicMock()
        task_mappings_mock.transform.return_value = []
        create_task_mappings_mock.return_value = task_mappings_mock
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        logger_mock = MagicMock()
        mongo_mock.task_mappings.return_value.insert_many.side_effect = TypeError(
            "documents must be a non-empty list"
        )
        work_item_mock = MagicMock(source_file_regex="src", module=None)

        under_test._run_create_task_mappings(
            evg_api_mock, mongo_mock, work_item_mock, None, None, logger_mock
        )

        mongo_mock.task_mappings.return_value.insert_many.assert_not_called()
        work_item_mock = MagicMock(source_file_regex="src", test_file_regex="test", module=None)


class TestProcessQueuedTestMappingWorkItems:
    @patch(ns("_process_one_test_mapping_work_item"))
    def test_analyze_runs_while_work_available(self, mock_process_one_test_mapping_work_item):
        n_work_items = 3
        mock_process_one_test_mapping_work_item.side_effect = [False] * n_work_items + [True]
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test.process_queued_test_mapping_work_items(evg_api_mock, mongo_mock, None, None)

        assert n_work_items + 1 == mock_process_one_test_mapping_work_item.call_count

    @patch(ns("_process_one_test_mapping_work_item"))
    def test_analyze_does_not_throw_exceptions(self, mock_process_one_test_mapping_work_item):
        mock_process_one_test_mapping_work_item.side_effect = ValueError("Unexpected Exception")
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test.process_queued_test_mapping_work_items(evg_api_mock, mongo_mock, None, None)


class TestProcessOneTestMappingWorkItem:
    @patch(ns("ProjectTestMappingWorkItem"))
    def test_returns_true_if_no_work(self, work_item_mock):
        work_item_mock.next.return_value = None
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        work_done = under_test._process_one_test_mapping_work_item(
            evg_api_mock, mongo_mock, None, None
        )

        assert work_done

    @patch(ns("ProjectTestMappingWorkItem"))
    @patch(ns("_run_create_test_mappings"))
    def test_work_items_completed_successfully_are_marked_complete(
        self, run_create_test_mappings_mock, work_item_mock
    ):
        work_item_mock.next.return_value = MagicMock()
        run_create_test_mappings_mock.return_value = True
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        work_done = under_test._process_one_test_mapping_work_item(
            evg_api_mock, mongo_mock, None, None
        )

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

        work_done = under_test._process_one_test_mapping_work_item(
            evg_api_mock, mongo_mock, None, None
        )

        work_item_mock.next.return_value.complete.assert_not_called()
        assert not work_done


class TestRunCreateTestMappings:
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
