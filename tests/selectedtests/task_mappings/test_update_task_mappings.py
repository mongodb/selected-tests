from unittest.mock import MagicMock, patch

import selectedtests.task_mappings.update_task_mappings as under_test

NS = "selectedtests.task_mappings.update_task_mappings"


def ns(relative_name):  # pylint: disable=invalid-name
    """Return a full name from a name relative to the test module"s name space."""
    return NS + "." + relative_name


class TestUpdateTaskMappingsSinceLastCommit:
    @patch(ns("update_task_mappings"))
    @patch(ns("generate_task_mappings"))
    @patch(ns("VersionLimit"))
    @patch(ns("ProjectConfig.get"))
    def test_task_mappings_are_updated(
        self,
        project_config_mock,
        version_limit_mock,
        generate_task_mappings_mock,
        update_task_mappings_mock,
    ):
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        my_version_limit = MagicMock()
        version_limit_mock.return_value = my_version_limit
        project_config_list = [
            {
                "project": "project-1",
                "task_config": {
                    "most_recent_version_analyzed": "version-1",
                    "source_file_regex": "^src",
                    "build_variant_regex": "^!",
                    "module": "module-1",
                    "module_source_file_regex": "^src",
                },
            }
        ]
        mongo_mock.project_config.return_value.find.return_value = project_config_list

        task_mappings_list = ["mock-mapping"]
        generate_task_mappings_mock.return_value = (
            task_mappings_list,
            "most-recent-version-analyzed",
        )

        under_test.update_task_mappings_since_last_commit(evg_api_mock, mongo_mock)

        generate_task_mappings_mock.assert_called_once_with(
            evg_api_mock,
            "project-1",
            my_version_limit,
            "^src",
            build_variant_pattern="^!",
            module_name="module-1",
            module_source_file_pattern="^src",
        )
        task_config_mock = project_config_mock.return_value.task_config
        task_config_mock.update_most_recent_version_analyzed.assert_called_once_with(
            "most-recent-version-analyzed"
        )
        project_config_mock.return_value.save.assert_called_once_with(mongo_mock.project_config())
        update_task_mappings_mock.assert_called_once_with(task_mappings_list, mongo_mock)


class TestUpdateTaskMappings:
    @patch(ns("UpdateOne"), autospec=True)
    def test_task_mappings_are_updated(self, update_one_mock):
        mongo_mock = MagicMock()

        source_file = "src/mongo/db/storage/storage_engine_init.h"
        source_file_seen_count = 1
        mapping = {
            "project": "mongodb-mongo-master",
            "repo": "mongo",
            "branch": "master",
            "source_file": source_file,
        }
        task = {
            "name": "query_fuzzer_standalone_3_enterprise-rhel-62-64-bit",
            "variant": "enterprise-rhel-62-64-bit",
            "flip_count": 1,
        }
        mappings = [
            dict(
                **mapping,
                **dict(
                    # source_file=source_file,
                    source_file_seen_count=source_file_seen_count,
                    tasks=[task],
                ),
            )
        ]

        under_test.update_task_mappings(mappings, mongo_mock)
        mongo_mock.task_mappings.return_value.update_one.assert_called_once_with(
            {"source_file": source_file},
            {"$set": mapping, "$inc": {"source_file_seen_count": source_file_seen_count}},
            upsert=True,
        )

        update_one_mock.assert_called_once_with(
            {"source_file": source_file, "name": task["name"], "variant": task["variant"]},
            {"$inc": {"flip_count": task["flip_count"]}},
            upsert=True,
        )
        mongo_mock.task_mappings_tasks.return_value.bulk_write.assert_called_once_with(
            [update_one_mock.return_value]
        )
