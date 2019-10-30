from flask import testing
import json

from unittest.mock import patch, MagicMock

NS = "selectedtests.app.controllers.project_test_mappings_controller"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


@patch(ns("ProjectTestMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_work_item_inserted(
    get_evg_project_mock, project_test_mapping_work_item_mock, app_client: testing.FlaskClient
):
    project = "valid-evergreen-project"
    get_evg_project_mock.return_value = MagicMock(identifier=project)
    project_test_mapping_work_item_mock.new_test_mappings.return_value.insert.return_value = True
    test_params = dict(
        source_file_regex="source-file-regex",
        test_file_regex="test-file-regex",
        module="module",
        module_source_file_regex="module-source-file-regex",
        module_test_file_regex="module-test-file-regex",
    )

    response = app_client.post(f"/projects/{project}/test-mappings", data=json.dumps(test_params))
    assert response.status_code == 200
    assert f"Work item added for project '{project}'" in response.get_data(as_text=True)


@patch(ns("ProjectTestMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_no_module_passed_in(
    get_evg_project_mock, project_test_mapping_work_item_mock, app_client: testing.FlaskClient
):
    project = "valid-evergreen-project"
    get_evg_project_mock.return_value = MagicMock(identifier=project)
    project_test_mapping_work_item_mock.new_test_mappings.return_value.insert.return_value = True
    test_params = dict(source_file_regex="source-file-regex", test_file_regex="test-file-regex")

    response = app_client.post(f"/projects/{project}/test-mappings", data=json.dumps(test_params))
    assert response.status_code == 200
    assert f"Work item added for project '{project}'" in response.get_data(as_text=True)


@patch(ns("get_evg_project"))
def test_project_not_found(get_evg_project_mock, app_client: testing.FlaskClient):
    get_evg_project_mock.return_value = None
    test_params = dict(source_file_regex="source-file-regex", test_file_regex="test-file-regex")

    response = app_client.post(
        "/projects/invalid-evergreen-project/test-mappings", data=json.dumps(test_params)
    )
    assert response.status_code == 404
    assert "Evergreen project not found" in response.get_data(as_text=True)


@patch(ns("ProjectTestMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_project_cannot_be_inserted(
    get_evg_project_mock, project_test_mapping_work_item_mock, app_client: testing.FlaskClient
):
    get_evg_project_mock.return_value = MagicMock()
    project_test_mapping_work_item_mock.new_test_mappings.return_value.insert.return_value = False
    test_params = dict(source_file_regex="source-file-regex", test_file_regex="test-file-regex")
    project = "project-already-exists-in-work-item-db"

    response = app_client.post(f"/projects/{project}/test-mappings", data=json.dumps(test_params))
    assert response.status_code == 422
    assert f"Work item already exists for project '{project}'" in response.get_data(as_text=True)
