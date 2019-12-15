import os
import re

from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

from selectedtests.test_mappings.commit_limit import CommitLimit
import selectedtests.test_mappings.create_test_mappings as under_test

NS = "selectedtests.test_mappings.create_test_mappings"
SOURCE_RE = re.compile(".*source")
TEST_RE = re.compile(".*test")
PROJECT = "my_project"
BRANCH = "master"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestCreateMappings:
    def test_no_source_files_changed(self, repo_with_no_source_files_changed):
        commit_limit_mock = MagicMock()
        commit_limit_mock.check_commit_before_limit.return_value = False

        with TemporaryDirectory() as tmpdir:
            repo = repo_with_no_source_files_changed(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, commit_limit_mock, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_one_source_file_and_no_test_files_changed(
        self, repo_with_one_source_file_and_no_test_files_changed
    ):
        commit_limit_mock = MagicMock()
        commit_limit_mock.check_commit_before_limit.return_value = False

        with TemporaryDirectory() as tmpdir:
            repo = repo_with_one_source_file_and_no_test_files_changed(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, commit_limit_mock, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_no_source_files_and_one_test_file_changed(
        self, repo_with_no_source_files_and_one_test_file_changed
    ):
        commit_limit_mock = MagicMock()
        commit_limit_mock.check_commit_before_limit.return_value = False

        with TemporaryDirectory() as tmpdir:
            repo = repo_with_no_source_files_and_one_test_file_changed(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, commit_limit_mock, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_one_source_file_and_one_test_file_changed_in_same_commit(
        self, repo_with_source_and_test_file_changed_in_same_commit
    ):
        commit_limit_mock = MagicMock()
        commit_limit_mock.check_commit_before_limit.return_value = False

        with TemporaryDirectory() as tmpdir:
            repo = repo_with_source_and_test_file_changed_in_same_commit(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, commit_limit_mock, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()

            source_file_test_mapping = test_mappings_list[0]
            assert source_file_test_mapping["source_file"] == "new-source-file"
            assert source_file_test_mapping["project"] == PROJECT
            assert source_file_test_mapping["repo"] == os.path.basename(tmpdir)
            assert source_file_test_mapping["branch"] == BRANCH
            assert source_file_test_mapping["source_file_seen_count"] == 1
            for test_file_mapping in source_file_test_mapping["test_files"]:
                assert test_file_mapping["name"] == "new-test-file"
                assert test_file_mapping["test_file_seen_count"] == 1

    def test_one_source_file_and_one_test_file_changed_in_different_commits(
        self, repo_with_source_and_test_file_changed_in_different_commits
    ):
        commit_limit_mock = MagicMock()
        commit_limit_mock.check_commit_before_limit.return_value = False

        with TemporaryDirectory() as tmpdir:
            repo = repo_with_source_and_test_file_changed_in_different_commits(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, commit_limit_mock, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_commit_range_includes_time_of_file_changes(self, repo_with_files_added_two_days_ago):
        commit_limit_mock = MagicMock()
        commit_limit_mock.check_commit_before_limit.return_value = False

        with TemporaryDirectory() as tmpdir:
            repo = repo_with_files_added_two_days_ago(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, commit_limit_mock, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()

            source_file_test_mapping = test_mappings_list[0]
            assert source_file_test_mapping["source_file"] == "new-source-file"
            for test_file_mapping in source_file_test_mapping["test_files"]:
                assert test_file_mapping["name"] == "new-test-file"
                assert test_file_mapping["test_file_seen_count"] == 1

    def test_commit_range_excludes_time_of_file_changes(self, repo_with_files_added_two_days_ago):
        commit_limit_mock = MagicMock()
        commit_limit_mock.check_commit_before_limit.return_value = True

        with TemporaryDirectory() as tmpdir:
            repo = repo_with_files_added_two_days_ago(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, commit_limit_mock, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0


class TestGenerateProjectTestMappings:
    @patch(ns("init_repo"))
    def test_generates_project_mappings(
        self,
        init_repo_mock,
        evg_projects,
        evg_versions,
        repo_with_source_and_test_file_changed_in_same_commit,
        expected_test_mappings,
    ):

        mock_evg_api = MagicMock()
        mock_evg_api.all_projects.return_value = evg_projects
        mock_evg_api.versions_by_project.return_value = evg_versions

        commit_limit_mock = MagicMock()
        commit_limit_mock.check_commit_before_limit.return_value = False

        with TemporaryDirectory() as tmpdir:
            repo = repo_with_source_and_test_file_changed_in_same_commit(tmpdir)
            init_repo_mock.return_value = repo
            commits = list(repo.iter_commits("master"))
            repo_newest_commit = commits[0]
            mappings, most_recent_commit_analyzed = under_test.generate_project_test_mappings(
                mock_evg_api, "mongodb-mongo-master", tmpdir, SOURCE_RE, TEST_RE, commit_limit_mock
            )

        assert most_recent_commit_analyzed == repo_newest_commit.hexsha

        assert len(mappings) == 1
        test_mapping = mappings[0]
        expected_test_mapping = expected_test_mappings[0]
        assert test_mapping["source_file"] == expected_test_mapping["source_file"]
        assert test_mapping["project"] == expected_test_mapping["project"]
        assert test_mapping["branch"] == expected_test_mapping["branch"]
        assert (
            test_mapping["source_file_seen_count"]
            == expected_test_mapping["source_file_seen_count"]
        )
        assert test_mapping["test_files"] == expected_test_mapping["test_files"]


class TestGenerateModuleTestMappings:
    @patch(ns("init_repo"))
    def test_generates_module_mappings(
        self,
        init_repo_mock,
        repo_with_source_and_test_file_changed_in_same_commit,
        expected_test_mappings,
        evg_versions_with_manifest,
    ):
        mock_evg_api = MagicMock()
        mock_evg_api.versions_by_project.return_value = evg_versions_with_manifest

        commit_limit_mock = MagicMock()
        commit_limit_mock.check_commit_before_limit.return_value = False

        with TemporaryDirectory() as tmpdir:
            repo = repo_with_source_and_test_file_changed_in_same_commit(tmpdir)
            init_repo_mock.return_value = repo
            commits = list(repo.iter_commits("master"))
            repo_newest_commit = commits[0]
            mappings, most_recent_commit_analyzed = under_test.generate_module_test_mappings(
                mock_evg_api,
                "mongodb-mongo-master",
                "my-module",
                tmpdir,
                SOURCE_RE,
                TEST_RE,
                commit_limit_mock,
            )

        assert most_recent_commit_analyzed == repo_newest_commit.hexsha

        assert len(mappings) == 1
        test_mapping = mappings[0]
        expected_test_mapping = expected_test_mappings[0]
        assert test_mapping["source_file"] == expected_test_mapping["source_file"]
        assert test_mapping["project"] == expected_test_mapping["project"]
        assert test_mapping["branch"] == "module-branch"
        assert (
            test_mapping["source_file_seen_count"]
            == expected_test_mapping["source_file_seen_count"]
        )
        assert test_mapping["test_files"] == expected_test_mapping["test_files"]


class TestGenerateTestMappings:
    @patch(ns("generate_project_test_mappings"))
    @patch(ns("generate_module_test_mappings"))
    def test_generates_mappings(
        self, generate_module_test_mappings_mock, generate_project_test_mappings_mock
    ):
        mock_evg_api = MagicMock()
        generate_project_test_mappings_mock.return_value = (
            ["mock-project-mappings"],
            "last-project-sha-analyzed",
        )
        generate_module_test_mappings_mock.return_value = (
            ["mock-module-mappings"],
            "last-module-sha-analyzed",
        )
        test_mappings_result = under_test.generate_test_mappings(
            mock_evg_api,
            "mongodb-mongo-master",
            CommitLimit(stop_at_commit_sha="some-project-commit-sha"),
            ".*src",
            ".*test",
            "my-module",
            CommitLimit(stop_at_commit_sha="some-module-commit-sha"),
            ".*src",
            ".*test",
        )
        assert test_mappings_result.test_mappings_list == [
            "mock-project-mappings",
            "mock-module-mappings",
        ]
        assert (
            test_mappings_result.most_recent_project_commit_analyzed == "last-project-sha-analyzed"
        )
        assert test_mappings_result.most_recent_module_commit_analyzed == "last-module-sha-analyzed"

    @patch(ns("generate_project_test_mappings"))
    def test_no_module_name_passed_in(self, generate_project_test_mappings_mock):
        mock_evg_api = MagicMock()
        generate_project_test_mappings_mock.return_value = (
            ["mock-project-mappings"],
            "last-project-sha-analyzed",
        )
        test_mappings_result = under_test.generate_test_mappings(
            mock_evg_api,
            "mongodb-mongo-master",
            CommitLimit(stop_at_commit_sha="some-project-commit-sha"),
            ".*src",
            ".*test",
        )
        assert test_mappings_result.test_mappings_list == ["mock-project-mappings"]
        assert (
            test_mappings_result.most_recent_project_commit_analyzed == "last-project-sha-analyzed"
        )
        assert not test_mappings_result.most_recent_module_commit_analyzed
