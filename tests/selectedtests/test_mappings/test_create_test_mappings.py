import os
import re
import pytz

from datetime import datetime, time, timedelta
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

import selectedtests.test_mappings.create_mappings as under_test

NS = "selectedtests.test_mappings.create_mappings"
SOURCE_RE = re.compile(".*source")
TEST_RE = re.compile(".*test")
ONE_DAY_AGO = datetime.combine(datetime.now() - timedelta(days=1), time()).replace(tzinfo=pytz.UTC)
ONE_DAY_FROM_NOW = datetime.combine(datetime.now() + timedelta(days=1), time()).replace(
    tzinfo=pytz.UTC
)
PROJECT = "my_project"
BRANCH = "master"
THREE_DAYS_AGO = datetime.combine(datetime.now() - timedelta(days=3), time()).replace(
    tzinfo=pytz.UTC
)
TWO_DAYS_AGO = datetime.combine(datetime.now() - timedelta(days=2), time()).replace(tzinfo=pytz.UTC)


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestTestMappings:
    def test_no_source_files_changed(self, repo_with_no_source_files_changed):
        with TemporaryDirectory() as tmpdir:
            repo = repo_with_no_source_files_changed(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_one_source_file_and_no_test_files_changed(
        self, repo_with_one_source_file_and_no_test_files_changed
    ):
        with TemporaryDirectory() as tmpdir:
            repo = repo_with_one_source_file_and_no_test_files_changed(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_no_source_files_and_one_test_file_changed(
        self, repo_with_no_source_files_and_one_test_file_changed
    ):
        with TemporaryDirectory() as tmpdir:
            repo = repo_with_no_source_files_and_one_test_file_changed(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_one_source_file_and_one_test_file_changed_in_same_commit(
        self, repo_with_one_source_file_and_one_test_file_changed_in_same_commit
    ):
        with TemporaryDirectory() as tmpdir:
            repo = repo_with_one_source_file_and_one_test_file_changed_in_same_commit(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
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
        self, repo_with_one_source_file_and_one_test_file_changed_in_different_commits
    ):
        with TemporaryDirectory() as tmpdir:
            repo = repo_with_one_source_file_and_one_test_file_changed_in_different_commits(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_date_range_includes_time_of_file_changes(self, repo_with_files_added_two_days_ago):
        with TemporaryDirectory() as tmpdir:
            repo = repo_with_files_added_two_days_ago(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, THREE_DAYS_AGO, TWO_DAYS_AGO, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()

            source_file_test_mapping = test_mappings_list[0]
            assert source_file_test_mapping["source_file"] == "new-source-file"
            for test_file_mapping in source_file_test_mapping["test_files"]:
                assert test_file_mapping["name"] == "new-test-file"
                assert test_file_mapping["test_file_seen_count"] == 1

    def test_date_range_excludes_time_of_file_changes(self, repo_with_files_added_two_days_ago):
        with TemporaryDirectory() as tmpdir:
            repo = repo_with_files_added_two_days_ago(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
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
        repo_with_files_added_two_days_ago,
        expected_test_mappings,
    ):

        mock_evg_api = MagicMock()
        mock_evg_api.all_projects.return_value = evg_projects
        mock_evg_api.versions_by_project.return_value = evg_versions

        with TemporaryDirectory() as tmpdir:
            init_repo_mock.return_value = repo_with_files_added_two_days_ago(tmpdir)
            mappings = under_test.generate_project_test_mappings(
                mock_evg_api,
                "mongodb-mongo-master",
                tmpdir,
                SOURCE_RE,
                TEST_RE,
                THREE_DAYS_AGO,
                TWO_DAYS_AGO,
            )
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
        repo_with_files_added_two_days_ago,
        expected_test_mappings,
        evg_versions_with_manifest,
    ):
        mock_evg_api = MagicMock()
        mock_evg_api.versions_by_project.return_value = evg_versions_with_manifest

        with TemporaryDirectory() as tmpdir:
            init_repo_mock.return_value = repo_with_files_added_two_days_ago(tmpdir)
            mappings = under_test.generate_module_test_mappings(
                mock_evg_api,
                "mongodb-mongo-master",
                "my-module",
                tmpdir,
                SOURCE_RE,
                TEST_RE,
                THREE_DAYS_AGO,
                TWO_DAYS_AGO,
            )
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
        generate_project_test_mappings_mock.return_value = ["mock-project-mappings"]
        generate_module_test_mappings_mock.return_value = ["mock-module-mappings"]
        mappings = under_test.generate_test_mappings(
            mock_evg_api,
            "mongodb-mongo-master",
            SOURCE_RE,
            TEST_RE,
            ONE_DAY_AGO,
            ONE_DAY_FROM_NOW,
            "my-module",
            SOURCE_RE,
            TEST_RE,
        )
        assert mappings == ["mock-project-mappings", "mock-module-mappings"]

    @patch(ns("generate_project_test_mappings"))
    def test_no_module_name_passed_in(self, generate_project_test_mappings_mock):
        mock_evg_api = MagicMock()
        generate_project_test_mappings_mock.return_value = ["mock-project-mappings"]
        mappings = under_test.generate_test_mappings(
            mock_evg_api, "mongodb-mongo-master", SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW
        )
        assert mappings == ["mock-project-mappings"]
