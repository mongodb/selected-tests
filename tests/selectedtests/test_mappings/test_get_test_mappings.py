from unittest.mock import MagicMock

import selectedtests.test_mappings.get_test_mappings as under_test


class TestGetCorrelatedTestMappings:
    def test_mappings_found(self):
        collection_mock = MagicMock()
        threshold = 0.5

        collection_mock.aggregate.return_value = ["results"]
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        test_mappings = under_test.get_correlated_test_mappings(
            collection_mock, changed_files, project, threshold
        )

        collection_mock.aggregate.assert_called_once()
        assert ["results"] == test_mappings

    def test_no_mappings_found(self):
        collection_mock = MagicMock()
        collection_mock.aggregate.return_value = []
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        test_mappings = under_test.get_correlated_test_mappings(
            collection_mock, changed_files, project, 0
        )

        assert test_mappings == []
        collection_mock.aggregate.assert_called_once()
