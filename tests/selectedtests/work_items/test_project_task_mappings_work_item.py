from datetime import datetime
from unittest.mock import MagicMock
from pymongo.errors import DuplicateKeyError

import selectedtests.work_items.project_task_mapping_work_item as under_test

PROJECT = "my-project"
SOURCE_FILE_REGEX = ".*source"
MODULE = "my-module"
MODULE_SOURCE_FILE_REGEX = ".*source"
BUILD_VARIANT_REGEX = "!.*"


class TestProjectTaskMappingWorkItem:
    def test_create_new_task_mappings(self):
        work_item = under_test.ProjectTaskMappingWorkItem.new_task_mappings(
            PROJECT, SOURCE_FILE_REGEX, MODULE, MODULE_SOURCE_FILE_REGEX, BUILD_VARIANT_REGEX
        )

        assert work_item.project == PROJECT
        assert work_item.source_file_regex == SOURCE_FILE_REGEX
        assert work_item.module == MODULE
        assert work_item.module_source_file_regex == MODULE_SOURCE_FILE_REGEX
        assert work_item.build_variant_regex == BUILD_VARIANT_REGEX
        assert isinstance(work_item.created_on, datetime)
        assert not work_item.start_time
        assert not work_item.end_time

    def test_no_module_passed_in(self):
        collection = MagicMock()
        collection.insert_one.return_value.acknowledged = True

        work_item = under_test.ProjectTaskMappingWorkItem.new_task_mappings(
            PROJECT, SOURCE_FILE_REGEX
        )
        new_item = work_item.insert(collection)

        collection.insert_one.assert_called_once()

        assert new_item

    def test_insert_adds_item_to_collection(self):
        collection = MagicMock()
        collection.insert_one.return_value.acknowledged = True

        work_item = under_test.ProjectTaskMappingWorkItem.new_task_mappings(
            PROJECT, SOURCE_FILE_REGEX, MODULE, MODULE_SOURCE_FILE_REGEX, BUILD_VARIANT_REGEX
        )
        new_item = work_item.insert(collection)

        collection.insert_one.assert_called_once()

        assert new_item

    def test_insert_fails_when_item_exists(self):
        collection = MagicMock()
        collection.insert_one.side_effect = DuplicateKeyError(
            "E11000 duplicate key error collection"
        )

        work_item = under_test.ProjectTaskMappingWorkItem.new_task_mappings(
            PROJECT, SOURCE_FILE_REGEX
        )
        new_item = work_item.insert(collection)

        collection.insert_one.assert_called_once()

        assert not new_item
