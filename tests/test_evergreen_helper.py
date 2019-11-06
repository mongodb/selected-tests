from unittest.mock import MagicMock
import selectedtests.evergreen_helper as under_test


class TestGetEvgProject:
    def test_project_exists(self):
        evg_api_mock = MagicMock()
        evg_api_mock.all_projects.return_value = [
            MagicMock(identifier=f"project_{i}", owner_name=f"owner_{i}") for i in range(3)
        ]
        project_name = "project_1"

        project = under_test.get_evg_project(evg_api_mock, project_name)
        assert project.identifier == project_name
        assert project.owner_name == "owner_1"

    def test_project_does_not_exist(self):
        evg_api_mock = MagicMock()
        evg_api_mock.all_projects.return_value = [
            MagicMock(identifier=f"project_{i}", owner_name=f"owner_{i}") for i in range(3)
        ]
        project_name = "project_4"

        project = under_test.get_evg_project(evg_api_mock, project_name)
        assert not project
