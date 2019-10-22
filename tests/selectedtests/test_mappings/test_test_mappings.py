import os
import re
import tempfile

from datetime import datetime, time, timedelta

import selectedtests.test_mappings.mappings as under_test

SOURCE_RE = re.compile(".*source")
TEST_RE = re.compile(".*test")
ONE_DAY_AGO = datetime.combine(datetime.now() - timedelta(days=1), time())
ONE_DAY_FROM_NOW = datetime.combine(datetime.now() + timedelta(days=1), time())
PROJECT = "my_project"
BRANCH = "master"


class TestTestMappings:
    def test_no_source_files_changed(self, repo_with_no_source_files_changed):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = repo_with_no_source_files_changed(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_one_source_file_and_no_test_files_changed(
        self, repo_with_one_source_file_and_no_test_files_changed
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = repo_with_one_source_file_and_no_test_files_changed(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_no_source_files_and_one_test_file_changed(
        self, repo_with_no_source_files_and_one_test_file_changed
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = repo_with_no_source_files_and_one_test_file_changed(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_one_source_file_and_one_test_file_changed_in_same_commit(
        self, repo_with_one_source_file_and_one_test_file_changed_in_same_commit
    ):
        with tempfile.TemporaryDirectory() as tmpdir:
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
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = repo_with_one_source_file_and_one_test_file_changed_in_different_commits(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0

    def test_date_range_includes_time_of_file_changes(self, repo_with_files_added_two_days_ago):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = repo_with_files_added_two_days_ago(tmpdir)
            three_days_ago = datetime.combine(datetime.now() - timedelta(days=3), time())
            two_days_ago = datetime.combine(datetime.now() - timedelta(days=2), time())
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, three_days_ago, two_days_ago, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()

            source_file_test_mapping = test_mappings_list[0]
            assert source_file_test_mapping["source_file"] == "new-source-file"
            for test_file_mapping in source_file_test_mapping["test_files"]:
                assert test_file_mapping["name"] == "new-test-file"
                assert test_file_mapping["test_file_seen_count"] == 1

    def test_date_range_excludes_time_of_file_changes(self, repo_with_files_added_two_days_ago):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = repo_with_files_added_two_days_ago(tmpdir)
            test_mappings = under_test.TestMappings.create_mappings(
                repo, SOURCE_RE, TEST_RE, ONE_DAY_AGO, ONE_DAY_FROM_NOW, PROJECT, BRANCH
            )
            test_mappings_list = test_mappings.get_mappings()
            assert len(test_mappings_list) == 0
