import selectedtests.test_mappings.get_test_mappings as under_test


class TestGetCorrelatedTestMappings:
    def test_mappings_found(self, mock_test_mappings):
        threshold = 0.5

        mock_test_mappings.aggregate.return_value = ["results"]
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        test_mappings = under_test.get_correlated_test_mappings(changed_files, project, threshold)

        mock_test_mappings.aggregate.assert_called_once()
        assert ["results"] == test_mappings

    def test_no_mappings_found(self, mock_test_mappings):
        mock_test_mappings.aggregate.return_value = []
        changed_files = ["src/file1.js", "src/file2.js"]
        project = "my-project"
        test_mappings = under_test.get_correlated_test_mappings(changed_files, project, 0)

        assert test_mappings == []
        mock_test_mappings.aggregate.assert_called_once()
