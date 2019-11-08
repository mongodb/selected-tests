from datetime import datetime
from unittest.mock import MagicMock
from pymongo.errors import DuplicateKeyError

import selectedtests.work_items.project_test_mapping_work_item as under_test

PROJECT = "my-project"
SOURCE_FILE_REGEX = ".*source"
TEST_FILE_REGEX = ".*test"
MODULE = "my-module"
MODULE_SOURCE_FILE_REGEX = ".*source"
MODULE_TEST_FILE_REGEX = ".*test"


class TestProjectTestMappingWorkItem:
    def test_create_new_test_mappings(self):
        work_item = under_test.ProjectTestMappingWorkItem.new_test_mappings(
            PROJECT,
            SOURCE_FILE_REGEX,
            TEST_FILE_REGEX,
            MODULE,
            MODULE_SOURCE_FILE_REGEX,
            MODULE_TEST_FILE_REGEX,
        )

        assert work_item.project == PROJECT
        assert work_item.source_file_regex == SOURCE_FILE_REGEX
        assert work_item.test_file_regex == TEST_FILE_REGEX
        assert work_item.module == MODULE
        assert work_item.module_source_file_regex == MODULE_SOURCE_FILE_REGEX
        assert work_item.module_test_file_regex == MODULE_TEST_FILE_REGEX
        assert isinstance(work_item.created_on, datetime)
        assert not work_item.start_time
        assert not work_item.end_time

    def test_no_module_passed_in(self):
        collection = MagicMock()
        collection.insert_one.return_value.acknowledged = True

        work_item = under_test.ProjectTestMappingWorkItem.new_test_mappings(
            PROJECT, SOURCE_FILE_REGEX, TEST_FILE_REGEX
        )
        new_item = work_item.insert(collection)

        collection.insert_one.assert_called_once()

        assert new_item

    def test_insert_adds_item_to_collection(self):
        collection = MagicMock()
        collection.insert_one.return_value.acknowledged = True

        work_item = under_test.ProjectTestMappingWorkItem.new_test_mappings(
            PROJECT, SOURCE_FILE_REGEX, TEST_FILE_REGEX
        )
        new_item = work_item.insert(collection)

        collection.insert_one.assert_called_once()

        assert new_item

    def test_insert_fails_when_item_exists(self):
        collection = MagicMock()
        collection.insert_one.side_effect = DuplicateKeyError(
            "E11000 duplicate key error collection"
        )

        work_item = under_test.ProjectTestMappingWorkItem.new_test_mappings(
            PROJECT, SOURCE_FILE_REGEX, TEST_FILE_REGEX
        )
        new_item = work_item.insert(collection)

        collection.insert_one.assert_called_once()

        assert not new_item

    def test_next_not_found(self):
        collection = MagicMock()
        collection.find_one_and_update.return_value = None

        work_item = under_test.ProjectTestMappingWorkItem.next(collection)

        assert not work_item

    def test_next_found_work(self):
        now = datetime.now()
        collection = MagicMock()
        collection.find_one_and_update.return_value = {
            "created_on": now,
            "project": "my-project",
            "source_file_regex": "my-source-file-regex",
            "test_file_regex": "my-test-file-regex",
            "module": "my-module",
            "module_source_file_regex": "my-module-source-file-regex",
            "module_test_file_regex": "my-module-test-file-regex",
            "start_time": None,
            "end_time": None,
        }

        work_item = under_test.ProjectTestMappingWorkItem.next(collection)

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
            "test_file_regex": "my-test-file-regex",
            "module": None,
            "module_source_file_regex": None,
            "module_test_file_regex": None,
            "start_time": None,
            "end_time": None,
        }

        work_item = under_test.ProjectTestMappingWorkItem.next(collection)

        assert work_item.project == "my-project"
        assert work_item.created_on == now
        assert not work_item.module
        assert not work_item.module_source_file_regex
        assert not work_item.module_test_file_regex
        assert not work_item.start_time
        assert not work_item.end_time
