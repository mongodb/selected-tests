from unittest.mock import MagicMock

import selectedtests.project_config as under_test


class TestTaskConfig:
    def test_update(self):
        task_config = under_test.TaskConfig()
        task_config.update("most-recent-version-analyzed", "^src", "^build", "my-module", "^src")

        assert task_config.most_recent_version_analyzed == "most-recent-version-analyzed"
        assert task_config.source_file_regex == "^src"
        assert task_config.build_variant_regex == "^build"
        assert task_config.module == "my-module"
        assert task_config.module_source_file_regex == "^src"

    def test_update_most_recent_version_analyzed(self):
        task_config = under_test.TaskConfig()
        task_config.update_most_recent_version_analyzed("most-recent-version-analyzed")

        assert task_config.most_recent_version_analyzed == "most-recent-version-analyzed"
        assert not task_config.source_file_regex


class TestTestConfig:
    def test_update(self):
        test_config = under_test.TestConfig()
        test_config.update(
            "last-project-sha-analyzed",
            "^src",
            "^test",
            "my-module",
            "last-module-sha-analyzed",
            "^src",
            "^test",
        )

        assert test_config.most_recent_project_commit_analyzed == "last-project-sha-analyzed"
        assert test_config.source_file_regex == "^src"
        assert test_config.test_file_regex == "^test"
        assert test_config.module == "my-module"
        assert test_config.most_recent_module_commit_analyzed == "last-module-sha-analyzed"
        assert test_config.module_source_file_regex == "^src"
        assert test_config.module_test_file_regex == "^test"

    def test_update_most_recent_commits_analyzed(self):
        test_config = under_test.TestConfig()
        test_config.update_most_recent_commits_analyzed(
            "last-project-sha-analyzed", "last-module-sha-analyzed"
        )

        assert test_config.most_recent_project_commit_analyzed == "last-project-sha-analyzed"
        assert test_config.most_recent_module_commit_analyzed == "last-module-sha-analyzed"
        assert not test_config.source_file_regex


class TestProjectConfig:
    def test_get_when_config_exists(self):
        collection_mock = MagicMock()
        collection_mock.find_one.return_value = {
            "project": "project-1",
            "task_config": {
                "most_recent_version_analyzed": "version-1",
                "source_file_regex": "^src",
                "build_variant_regex": "^!",
                "module": "module-1",
                "module_source_file_regex": "^src",
            },
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
        project_config = under_test.ProjectConfig.get(collection_mock, "project-1")

        assert project_config.project == "project-1"
        assert type(project_config.task_config) == under_test.TaskConfig
        assert project_config.task_config.most_recent_version_analyzed == "version-1"
        assert type(project_config.test_config) == under_test.TestConfig
        assert project_config.test_config.most_recent_project_commit_analyzed == "project-sha-1"

    def test_get_when_config_doesnt_exist(self):
        collection_mock = MagicMock()
        collection_mock.find_one.return_value = None
        project_config = under_test.ProjectConfig.get(collection_mock, "project-1")

        assert project_config.project == "project-1"
        assert type(project_config.task_config) == under_test.TaskConfig
        assert not project_config.task_config.most_recent_version_analyzed
        assert type(project_config.test_config) == under_test.TestConfig
        assert not project_config.test_config.most_recent_project_commit_analyzed

    def test_save(self):
        collection_mock = MagicMock()
        collection_mock.find_one.return_value = None
        project_config = under_test.ProjectConfig.get(collection_mock, "project-1")

        project_config.save(collection_mock)

        collection_mock.update.assert_called_once()
