from datetime import datetime
from unittest.mock import MagicMock
from pymongo.errors import DuplicateKeyError

import selectedtests.work_items.task_mapping_work_item as under_test

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

    def test_next_not_found(self):
        collection = MagicMock()
        collection.find_one_and_update.return_value = None

        work_item = under_test.ProjectTaskMappingWorkItem.next(collection)

        assert not work_item

    def test_next_found_work(self):
        now = datetime.now()
        collection = MagicMock()
        collection.find_one_and_update.return_value = {
            "created_on": now,
            "project": "my-project",
            "source_file_regex": "my-source-file-regex",
            "module": "my-module",
            "module_source_file_regex": "my-module-source-file-regex",
            "build_variant_regex": "!",
            "start_time": None,
            "end_time": None,
        }

        work_item = under_test.ProjectTaskMappingWorkItem.next(collection)

        assert work_item.project == "my-project"
        assert work_item.created_on == now
        assert not work_item.start_time
        assert not work_item.end_time

    def test_next_with_missing_fields(self):
        now = datetime.now()
        collection = MagicMock()
        collection.find_one_and_update.return_value = {
            "created_on": now,
            "project": "my-project",
            "source_file_regex": "my-source-file-regex",
            "module": None,
            "module_source_file_regex": None,
            "build_variant_regex": None,
            "start_time": None,
            "end_time": None,
        }

        work_item = under_test.ProjectTaskMappingWorkItem.next(collection)

        assert work_item.project == "my-project"
        assert work_item.created_on == now
        assert not work_item.module
        assert not work_item.module_source_file_regex
        assert not work_item.build_variant_regex
        assert not work_item.start_time
        assert not work_item.end_time
