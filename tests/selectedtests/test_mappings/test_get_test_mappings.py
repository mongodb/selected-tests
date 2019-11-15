from unittest.mock import MagicMock

import selectedtests.test_mappings.get_mappings as under_test
from bson import json_util


class TestGetCorrelatedTestMappings:
    def test_mappings_found(self):
        collection_mock = MagicMock()
        collection_mock.find.side_effect = [
            [{"project": "my_project", "source_file": "src/file1.js"}],
            [{"project": "my_project", "source_file": "src/file2.js"}],
        ]
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        test_mappings = under_test.get_correlated_test_mappings(
            collection_mock, changed_files, project
        )

        assert test_mappings == json_util.dumps(
            [
                {"project": "my_project", "source_file": "src/file1.js"},
                {"project": "my_project", "source_file": "src/file2.js"},
            ]
        )

    def test_no_mappings_found(self):
        collection_mock = MagicMock()
        collection_mock.find.return_value = []
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        test_mappings = under_test.get_correlated_test_mappings(
            collection_mock, changed_files, project
        )

        assert test_mappings == json_util.dumps([])
