from unittest.mock import MagicMock

import selectedtests.test_mappings.get_mappings as under_test
from bson import json_util


class TestGetCorrelatedTestMappings:
    def test_mappings_found(self):
        collection_mock = MagicMock()
        test_mapping = {
            "project": "my_project",
            "source_file": "src/file1.js",
            "source_file_seen_count": 1,
            "test_files": [
                {"name": "test_file_above_threshold.js", "test_file_seen_count": 1},
                {"name": "test_file_below_threshold.js", "test_file_seen_count": 1},
            ],
        }
        collection_mock.find.side_effect = [[test_mapping]]
        changed_files = ["src/file1.js"]
        project = "my-project"
        test_mappings = under_test.get_correlated_test_mappings(
            collection_mock, changed_files, project, 0
        )

        assert test_mappings == json_util.dumps([test_mapping])

    def test_mappings_filtered(self):
        collection_mock = MagicMock()
        threshold = 0.5
        test_mapping_1 = {
            "project": "my_project",
            "source_file": "src/file1.js",
            "source_file_seen_count": 3,
            "test_files": [
                {"name": "test_file_above_threshold.js", "test_file_seen_count": 2},
                {"name": "test_file_below_threshold.js", "test_file_seen_count": 1},
            ],
        }
        test_mapping_2 = {
            "project": "my_project",
            "source_file": "src/file2.js",
            "source_file_seen_count": 1,
            "test_files": [{"name": "test1.js", "test_file_seen_count": 1}],
        }
        collection_mock.find.side_effect = [[test_mapping_1], [test_mapping_2]]
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        test_mappings = under_test.get_correlated_test_mappings(
            collection_mock, changed_files, project, threshold
        )

        test_mapping_1_with_test_file_excluded = {
            "project": "my_project",
            "source_file": "src/file1.js",
            "source_file_seen_count": 3,
            "test_files": [{"name": "test_file_above_threshold.js", "test_file_seen_count": 2}],
        }
        assert test_mappings == json_util.dumps(
            [test_mapping_1_with_test_file_excluded, test_mapping_2]
        )

    def test_no_mappings_found(self):
        collection_mock = MagicMock()
        collection_mock.find.return_value = []
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        test_mappings = under_test.get_correlated_test_mappings(
            collection_mock, changed_files, project, 0
        )

        assert test_mappings == json_util.dumps([])
