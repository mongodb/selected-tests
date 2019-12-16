from unittest.mock import MagicMock, patch

import selectedtests.work_items.process_task_mapping_work_items as under_test


NS = "selectedtests.work_items.process_task_mapping_work_items"


def ns(relative_name):  # pylint: disable=invalid-name
    """Return a full name from a name relative to the test module"s name space."""
    return NS + "." + relative_name


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

        under_test.process_queued_task_mapping_work_items(evg_api_mock, mongo_mock, after_date=None)

        assert n_work_items == mock_process_one_task_mapping_work_item.call_count

    @patch(ns("_process_one_task_mapping_work_item"))
    def test_analyze_does_not_throw_exceptions(self, mock_process_one_task_mapping_work_item):
        mock_process_one_task_mapping_work_item.side_effect = ValueError("Unexpected Exception")
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test.process_queued_task_mapping_work_items(evg_api_mock, mongo_mock, after_date=None)


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
    @patch(ns("_seed_task_mappings_for_project"))
    def test_work_items_completed_successfully_are_marked_complete(
        self, run_generate_task_mappings_mock
    ):
        work_item_mock = MagicMock()
        run_generate_task_mappings_mock.return_value = True
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test._process_one_task_mapping_work_item(
            work_item_mock, evg_api_mock, mongo_mock, after_date=None
        )

        work_item_mock.complete.assert_called_once()

    @patch(ns("_seed_task_mappings_for_project"))
    def test_work_items_completed_unsuccessfully_are_marked_not_complete(
        self, run_generate_task_mappings_mock
    ):
        work_item_mock = MagicMock()
        run_generate_task_mappings_mock.return_value = False
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test._process_one_task_mapping_work_item(
            work_item_mock, evg_api_mock, mongo_mock, after_date=None
        )

        work_item_mock.next.return_value.complete.assert_not_called()


class TestSeedTaskMappingsForProject:
    @patch(ns("generate_task_mappings"))
    @patch(ns("ProjectConfig.get"))
    def test_task_mappings_are_created(self, project_config_mock, generate_task_mappings_mock):
        generate_task_mappings_mock.return_value = (
            ["mock-response"],
            "most-recent-version-analyzed",
        )
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        logger_mock = MagicMock()
        work_item_mock = MagicMock(source_file_regex="src", module=None)

        under_test._seed_task_mappings_for_project(
            evg_api_mock, mongo_mock, work_item_mock, after_date=None, log=logger_mock
        )

        project_config_mock.return_value.task_config.update.assert_called_once_with(
            "most-recent-version-analyzed",
            work_item_mock.source_file_regex,
            work_item_mock.build_variant_regex,
            work_item_mock.module,
            work_item_mock.module_source_file_regex,
        )
        project_config_mock.return_value.save.assert_called_once_with(mongo_mock.project_config())
        mongo_mock.task_mappings.return_value.insert_many.assert_called_once_with(["mock-response"])

    @patch(ns("generate_task_mappings"))
    @patch(ns("ProjectConfig.get"))
    def test_no_task_mappings_are_created(self, project_config_mock, generate_task_mappings_mock):
        generate_task_mappings_mock.return_value = ([], "most-recent-version-analyzed")
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        logger_mock = MagicMock()
        mongo_mock.task_mappings.return_value.insert_many.side_effect = TypeError(
            "documents must be a non-empty list"
        )
        work_item_mock = MagicMock(source_file_regex="src", module=None)

        under_test._seed_task_mappings_for_project(
            evg_api_mock, mongo_mock, work_item_mock, after_date=None, log=logger_mock
        )

        project_config_mock.return_value.task_config.update.assert_called_once_with(
            "most-recent-version-analyzed",
            work_item_mock.source_file_regex,
            work_item_mock.build_variant_regex,
            work_item_mock.module,
            work_item_mock.module_source_file_regex,
        )
        project_config_mock.return_value.save.assert_called_once_with(mongo_mock.project_config())
        mongo_mock.task_mappings.return_value.insert_many.assert_not_called()
