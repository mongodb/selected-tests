import selectedtests.work_items.process_task_mapping_work_items as under_test
from unittest.mock import MagicMock, patch


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
    def test_task_mappings_are_created(self, generate_task_mappings_mock):
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

        mongo_mock.task_mappings_project_config.return_value.insert_one.assert_called_once_with(
            {
                "project": work_item_mock.project,
                "most_recent_version_analyzed": "most-recent-version-analyzed",
                "source_re": work_item_mock.source_file_regex,
                "build_re": work_item_mock.build_variant_regex,
                "module": work_item_mock.module,
                "module_source_re": work_item_mock.module_source_file_regex,
            }
        )
        mongo_mock.task_mappings.return_value.insert_many.assert_called_once_with(["mock-response"])

    @patch(ns("generate_task_mappings"))
    def test_no_task_mappings_are_created(self, generate_task_mappings_mock):
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

        mongo_mock.task_mappings_project_config.return_value.insert_one.assert_called_once_with(
            {
                "project": work_item_mock.project,
                "most_recent_version_analyzed": "most-recent-version-analyzed",
                "source_re": work_item_mock.source_file_regex,
                "build_re": work_item_mock.build_variant_regex,
                "module": work_item_mock.module,
                "module_source_re": work_item_mock.module_source_file_regex,
            }
        )
        mongo_mock.task_mappings.return_value.insert_many.assert_not_called()


class TestUpdateTaskMappingsSinceLastCommit:
    @patch(ns("generate_task_mappings"))
    @patch(ns("VersionLimit"))
    def test_task_mappings_are_updated(self, version_limit_mock, generate_task_mappings_mock):
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        my_version_limit = MagicMock()
        version_limit_mock.return_value = my_version_limit
        project_config_list = [
            {
                "project": "project-1",
                "most_recent_version_analyzed": "version-1",
                "source_re": "^src",
                "build_re": "^!",
                "module": "module-1",
                "module_source_re": "^src",
            }
        ]
        mongo_mock.task_mappings_project_config.return_value.find.return_value = project_config_list

        generate_task_mappings_mock.return_value = (
            ["mock-mapping"],
            "most-recent-version-analyzed",
        )

        under_test.update_task_mappings_since_last_commit(evg_api_mock, mongo_mock)

        generate_task_mappings_mock.assert_called_once_with(
            evg_api_mock,
            "project-1",
            my_version_limit,
            "^src",
            build_variant_regex="^!",
            module_name="module-1",
            module_source_file_regex="^src",
        )
        mongo_mock.task_mappings_project_config.return_value.update_one.assert_called_once_with(
            {"project": "project-1"},
            {"$set": {"most_recent_version_analyzed": "most-recent-version-analyzed"}},
        )
        mongo_mock.task_mappings.return_value.insert_many.assert_called_once_with(["mock-mapping"])
