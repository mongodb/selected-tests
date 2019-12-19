from unittest.mock import MagicMock, patch

import selectedtests.task_mappings.update_task_mappings as under_test

NS = "selectedtests.task_mappings.update_task_mappings"


def ns(relative_name):  # pylint: disable=invalid-name
    """Return a full name from a name relative to the test module"s name space."""
    return NS + "." + relative_name


class TestUpdateTaskMappingsSinceLastCommit:
    @patch(ns("generate_task_mappings"))
    @patch(ns("VersionLimit"))
    @patch(ns("ProjectConfig.get"))
    def test_task_mappings_are_updated(
        self, project_config_mock, version_limit_mock, generate_task_mappings_mock
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
            build_variant_pattern="^!",
            module_name="module-1",
            module_source_file_pattern="^src",
        )
        task_config_mock = project_config_mock.return_value.task_config
        task_config_mock.update_most_recent_version_analyzed.assert_called_once_with(
            "most-recent-version-analyzed"
        )
        project_config_mock.return_value.save.assert_called_once_with(mongo_mock.project_config())
        mongo_mock.task_mappings.return_value.insert_many.assert_called_once_with(["mock-mapping"])
