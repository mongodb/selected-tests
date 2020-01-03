from unittest.mock import MagicMock

import selectedtests.task_mappings.get_task_mappings as under_test


class TestGetCorrelatedTaskMappings:
    def task_mappings_found(self):
        collection_mock = MagicMock()
        task_mapping = {
            "project": "my_project",
            "source_file": "src/file1.js",
            "source_file_seen_count": 1,
            "tasks": [
                {"name": "test1.js", "variant": "my-variant", "flip_count": 1},
                {"name": "test2.js", "variant": "my-variant", "flip_count": 1},
            ],
        }
        collection_mock.find.side_effect = [[task_mapping]]
        changed_files = ["src/file1.js"]
        project = "my-project"
        task_mappings = under_test.get_correlated_task_mappings(
            collection_mock, changed_files, project, 0
        )

        assert task_mappings == [task_mapping]

    def task_mappings_filtered(self):
        collection_mock = MagicMock()
        threshold = 0.5
        task_mapping_1 = {
            "project": "my_project",
            "source_file": "src/file1.js",
            "source_file_seen_count": 3,
            "tasks": [
                {"name": "test_file_above_threshold.js", "variant": "my-variant", "flip_count": 2},
                {"name": "test_file_below_threshold.js", "variant": "my-variant", "flip_count": 1},
            ],
        }
        task_mapping_2 = {
            "project": "my_project",
            "source_file": "src/file2.js",
            "source_file_seen_count": 1,
            "test_files": [{"name": "test1.js", "test_file_seen_count": 1}],
        }
        collection_mock.find.side_effect = [[task_mapping_1], [task_mapping_2]]
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        task_mappings = under_test.get_correlated_task_mappings(
            collection_mock, changed_files, project, threshold
        )

        task_mapping_1_with_test_file_excluded = {
            "project": "my_project",
            "source_file": "src/file1.js",
            "source_file_seen_count": 3,
            "tasks": [
                {"name": "test_file_above_threshold.js", "variant": "my-variant", "flip_count": 2}
            ],
        }
        assert task_mappings == [task_mapping_1_with_test_file_excluded, task_mapping_2]

    def test_no_mappings_found(self):
        collection_mock = MagicMock()
        collection_mock.find.return_value = []
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        task_mappings = under_test.get_correlated_task_mappings(
            collection_mock, changed_files, project, 0
        )

        assert task_mappings == []
