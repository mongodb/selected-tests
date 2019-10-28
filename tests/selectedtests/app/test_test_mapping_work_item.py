from datetime import datetime
from unittest.mock import MagicMock
from pymongo.errors import DuplicateKeyError

import selectedtests.app.test_mapping_work_item as under_test

PROJECT = "my-project"
SOURCE_FILE_REGEX = ".*source"
TEST_FILE_REGEX = ".*test"
MODULE = "my-module"
MODULE_SOURCE_FILE_REGEX = ".*source"
MODULE_TEST_FILE_REGEX = ".*test"


class TestSetupIndexes:
    def test_indexes_created(self):
        collection = MagicMock()

        under_test.setup_indexes(collection)

        collection.create_indexes.assert_called_once()


class TestTestMappingWorkItem:
    def test_create_new_test_mappings(self):
        work_item = under_test.TestMappingWorkItem.new_test_mappings(
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

        work_item = under_test.TestMappingWorkItem.new_test_mappings(
            PROJECT, SOURCE_FILE_REGEX, TEST_FILE_REGEX
        )
        new_item = work_item.insert(collection)

        collection.insert_one.assert_called_once()

        assert new_item

    def test_insert_adds_item_to_collection(self):
        collection = MagicMock()
        collection.insert_one.return_value.acknowledged = True

        work_item = under_test.TestMappingWorkItem.new_test_mappings(
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

        work_item = under_test.TestMappingWorkItem.new_test_mappings(
            PROJECT, SOURCE_FILE_REGEX, TEST_FILE_REGEX
        )
        new_item = work_item.insert(collection)

        collection.insert_one.assert_called_once()

        assert not new_item
