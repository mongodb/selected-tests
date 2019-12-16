from unittest.mock import MagicMock, patch

from selectedtests.test_mappings.create_test_mappings import TestMappingsResult
import selectedtests.test_mappings.update_test_mappings as under_test


NS = "selectedtests.test_mappings.update_test_mappings"


def ns(relative_name):  # pylint: disable=invalid-name
    """Return a full name from a name relative to the test module"s name space."""
    return NS + "." + relative_name


class TestUpdateTestMappingsSinceLastCommit:
    @patch(ns("generate_test_mappings"))
    @patch(ns("CommitLimit"))
    def test_mappings_are_updated(self, commit_limit_mock, generate_test_mappings_mock):
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        my_commit_limit = MagicMock()
        commit_limit_mock.return_value = my_commit_limit
        project_config_list = [
            {
                "project": "project-1",
                "most_recent_project_commit_analyzed": "project-sha-1",
                "source_re": "^src",
                "test_re": "^jstests",
                "module": "module-1",
                "most_recent_module_commit_analyzed": "module-sha-2",
                "module_source_re": "^src",
                "module_test_re": "^jstests",
            }
        ]
        mongo_mock.test_mappings_project_config.return_value.find.return_value = project_config_list
        generate_test_mappings_mock.return_value = TestMappingsResult(
            test_mappings_list=["mock-mapping"],
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
            module_source_file_regex="^src",
            module_test_file_regex="^src",
        )
        mongo_mock.test_mappings_project_config.return_value.update_one.assert_called_once_with(
            {"project": "project-1"},
            {
                "$set": {
                    "most_recent_project_commit_analyzed": "last-project-sha-analyzed",
                    "most_recent_module_commit_analyzed": "last-module-sha-analyzed",
                }
            },
        )
        mongo_mock.test_mappings.return_value.insert_many.assert_called_once_with(["mock-mapping"])
