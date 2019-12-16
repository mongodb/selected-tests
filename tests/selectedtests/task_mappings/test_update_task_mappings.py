from unittest.mock import MagicMock, patch

import selectedtests.task_mappings.update_task_mappings as under_test


NS = "selectedtests.task_mappings.update_task_mappings"


def ns(relative_name):  # pylint: disable=invalid-name
    """Return a full name from a name relative to the test module"s name space."""
    return NS + "." + relative_name


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
            build_variant_pattern="^!",
            module_name="module-1",
            module_source_file_pattern="^src",
        )
        mongo_mock.task_mappings_project_config.return_value.update_one.assert_called_once_with(
            {"project": "project-1"},
            {"$set": {"most_recent_version_analyzed": "most-recent-version-analyzed"}},
        )
        mongo_mock.task_mappings.return_value.insert_many.assert_called_once_with(["mock-mapping"])
