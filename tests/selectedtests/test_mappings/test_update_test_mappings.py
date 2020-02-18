from unittest.mock import MagicMock, patch

import pytest

from pymongo import ReturnDocument
from pymongo.errors import BulkWriteError

import selectedtests.test_mappings.update_test_mappings as under_test

from selectedtests.test_mappings.create_test_mappings import TestMappingsResult

NS = "selectedtests.test_mappings.update_test_mappings"


def ns(relative_name):  # pylint: disable=invalid-name
    """Return a full name from a name relative to the test module"s name space."""
    return NS + "." + relative_name


class TestUpdateTestMappingsSinceLastCommit:
    @patch(ns("update_test_mappings"))
    @patch(ns("generate_test_mappings"))
    @patch(ns("CommitLimit"))
    @patch(ns("ProjectConfig.get"))
    def test_mappings_are_updated(
        self,
        project_config_mock,
        commit_limit_mock,
        generate_test_mappings_mock,
        update_test_mappings_mock,
    ):
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        my_commit_limit = MagicMock()
        commit_limit_mock.return_value = my_commit_limit
        project_config_list = [
            {
                "project": "project-1",
                "test_config": {
                    "most_recent_project_commit_analyzed": "project-sha-1",
                    "source_file_regex": "^src",
                    "test_file_regex": "^jstests",
                    "module": "module-1",
                    "most_recent_module_commit_analyzed": "module-sha-2",
                    "module_source_file_regex": "^src",
                    "module_test_file_regex": "^jstests",
                },
            }
        ]
        mongo_mock.project_config.return_value.find.return_value = project_config_list
        test_mappings_list = ["mock-mapping"]
        generate_test_mappings_mock.return_value = TestMappingsResult(
            test_mappings_list=test_mappings_list,
            most_recent_project_commit_analyzed="last-project-sha-analyzed",
            most_recent_module_commit_analyzed="last-module-sha-analyzed",
        )

        under_test.update_test_mappings_since_last_commit(evg_api_mock, mongo_mock)

        generate_test_mappings_mock.assert_called_once_with(
            evg_api_mock,
            "project-1",
            my_commit_limit,
            "^src",
            "^jstests",
            module_commit_limit=my_commit_limit,
            module_name="module-1",
            module_source_file_pattern="^src",
            module_test_file_pattern="^src",
        )
        test_config_mock = project_config_mock.return_value.test_config
        test_config_mock.update_most_recent_commits_analyzed.assert_called_once_with(
            "last-project-sha-analyzed", "last-module-sha-analyzed"
        )
        project_config_mock.return_value.save.assert_called_once_with(mongo_mock.project_config())
        update_test_mappings_mock.assert_called_once_with(test_mappings_list, mongo_mock)


class TestUpdateTestMappings:
    @patch(ns("update_test_mappings_test_files"), autospec=True)
    def test_mappings_are_updated(self, update_test_mappings_test_files_mock):
        mongo_mock = MagicMock()

        source_file_seen_count = 1
        query = {
            "project": "mongodb-mongo-master",
            "repo": "mongo",
            "branch": "master",
            "source_file": "src/mongo/db/storage/storage_engine_init.h",
        }
        test_file = {
            "name": "jstests/core/txns/commands_not_allowed_in_txn.js",
            "test_file_seen_count": 1,
        }
        mappings = [
            dict(
                **query,
                **dict(source_file_seen_count=source_file_seen_count, test_files=[test_file]),
            )
        ]

        mongo_mock.test_mappings.return_value.find_one_and_update.return_value = {"_id": 1}

        under_test.update_test_mappings(mappings, mongo_mock)
        mongo_mock.test_mappings.return_value.find_one_and_update.assert_called_once_with(
            query,
            {"$inc": {"source_file_seen_count": source_file_seen_count}},
            projection={"_id": 1},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

        update_test_mappings_test_files_mock.assert_called_once_with(
            [test_file], {"test_mapping_id": 1}, mongo_mock
        )


class TestUpdateTestMappingsTestFiles:
    @patch(ns("UpdateOne"), autospec=True)
    def test_test_mappings_test_files_are_updated(self, update_one_mock):
        mongo_mock = MagicMock()

        test_mapping_id = {"test_mapping_id": 1}
        test_file = {
            "name": "jstests/core/txns/commands_not_allowed_in_txn.js",
            "test_file_seen_count": 1,
        }

        under_test.update_test_mappings_test_files([test_file], test_mapping_id, mongo_mock)
        update_one_mock.assert_called_once_with(
            {"name": test_file["name"], "test_mapping_id": 1},
            {"$inc": {"test_file_seen_count": test_file["test_file_seen_count"]}},
            upsert=True,
        )

        mongo_mock.test_mappings_test_files.return_value.bulk_write.assert_called_once_with(
            [update_one_mock.return_value]
        )

    @patch(ns("LOGGER.exception"), autospec=True)
    @patch(ns("UpdateOne"), autospec=True)
    def test_task_mappings_exceptions(self, update_one_mock, exception_mock):
        mongo_mock = MagicMock()

        test_mapping_id = {"test_mapping_id": 1}
        test_file = {
            "name": "jstests/core/txns/commands_not_allowed_in_txn.js",
            "test_file_seen_count": 1,
        }

        details = {"errorLabels": []}
        mongo_mock.test_mappings_test_files.return_value.bulk_write.side_effect = BulkWriteError(
            details
        )
        pytest.raises(
            BulkWriteError,
            under_test.update_test_mappings_test_files,
            [test_file],
            test_mapping_id,
            mongo_mock,
        )
        exception_mock.assert_called_once_with(
            "bulk_write error",
            parent=test_mapping_id,
            operations=[update_one_mock.return_value],
            details=details,
        )
