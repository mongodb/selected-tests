from unittest.mock import MagicMock

import selectedtests.evergreen_helper as under_test

NS = "selectedtests.evergreen_helper"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


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


class TestGetEvgModuleForProject:
    def test_module_exists(self, evg_versions_with_manifest):
        mock_evg_api = MagicMock()
        mock_evg_api.versions_by_project.return_value = evg_versions_with_manifest
        module = under_test.get_evg_module_for_project(
            mock_evg_api, "mongodb-mongo-master", "my-module"
        )

        assert module.repo == "module-repo"
        assert module.branch == "module-branch"
        assert module.owner == "module-owner"

    def test_module_does_not_exist(self, evg_versions_with_manifest):
        mock_evg_api = MagicMock()

        version_mock = MagicMock()
        version_mock.get_manifest.return_value = MagicMock(modules={"not-my-module": MagicMock()})
        versions = [version_mock]
        mock_evg_api.versions_by_project.return_value = (v for v in versions)

        module = under_test.get_evg_module_for_project(
            mock_evg_api, "mongodb-mongo-master", "my-module"
        )

        assert not module
