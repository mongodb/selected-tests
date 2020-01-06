import json

from unittest.mock import MagicMock, patch

from flask import testing

NS = "selectedtests.app.controllers.project_task_mappings_controller"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


@patch(ns("get_correlated_task_mappings"))
@patch(ns("get_evg_project"))
def test_GET_task_mappings_found_with_threshold_param(
    get_evg_project_mock, get_correlated_task_mappings_mock, app_client: testing.FlaskClient
):
    project = "valid-evergreen-project"
    get_evg_project_mock.return_value = MagicMock(identifier=project)
    get_correlated_task_mappings_mock.return_value = ["task_mapping_1", "task_mapping_2"]

    response = app_client.get(
        f"/projects/{project}/task-mappings?changed_files=src/file1.js,src/file2.js&threshold=.5"
    )
    assert response.status_code == 200
    assert response.get_json() == {"task_mappings": ["task_mapping_1", "task_mapping_2"]}


@patch(ns("get_correlated_task_mappings"))
@patch(ns("get_evg_project"))
def test_GET_task_mappings_found_without_threshold_param(
    get_evg_project_mock, get_correlated_task_mappings_mock, app_client: testing.FlaskClient
):
    project = "valid-evergreen-project"
    get_evg_project_mock.return_value = MagicMock(identifier=project)
    get_correlated_task_mappings_mock.return_value = ["task_mapping_1", "task_mapping_2"]

    response = app_client.get(
        f"/projects/{project}/task-mappings?changed_files=src/file1.js,src/file2.js"
    )
    assert response.status_code == 200
    assert response.get_json() == {"task_mappings": ["task_mapping_1", "task_mapping_2"]}


@patch(ns("get_correlated_task_mappings"))
@patch(ns("get_evg_project"))
def test_GET_missing_changed_files_query_param(
    get_evg_project_mock, get_correlated_task_mappings_mock, app_client: testing.FlaskClient
):
    project = "valid-evergreen-project"

    response = app_client.get(f"/projects/{project}/task-mappings")
    assert response.status_code == 400
    assert response.get_json()["custom"] == "Missing changed_files query param"


@patch(ns("get_correlated_task_mappings"))
@patch(ns("get_evg_project"))
def test_GET_project_not_found(
    get_evg_project_mock, get_correlated_task_mappings_mock, app_client: testing.FlaskClient
):
    get_evg_project_mock.return_value = None

    response = app_client.get(
        f"/projects/invalid-evergreen-project/task-mappings?changed_files=src/file1.js,src/file2.js"
    )
    assert response.status_code == 404
    assert response.get_json()["custom"] == "Evergreen project not found"


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_POST_work_item_inserted(
    get_evg_project_mock, project_task_mapping_work_item_mock, app_client: testing.FlaskClient
):
    project = "valid-evergreen-project"
    get_evg_project_mock.return_value = MagicMock(identifier=project)
    project_task_mapping_work_item_mock.new_task_mappings.return_value.insert.return_value = True
    test_params = dict(
        source_file_regex="source-file-regex",
        module="module",
        module_source_file_regex="module-source-file-regex",
        build_variant_regex="!.*",
    )

    response = app_client.post(
        f"/projects/{project}/task-mappings",
        data=json.dumps(test_params),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.get_json()["custom"] == f"Work item added for project '{project}'"


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_POST_work_item_inserted_with_incorrect_params(
    get_evg_project_mock, project_task_mapping_work_item_mock, app_client: testing.FlaskClient
):
    project = "valid-evergreen-project"
    get_evg_project_mock.return_value = MagicMock(identifier=project)
    project_task_mapping_work_item_mock.new_task_mappings.return_value.insert.return_value = True
    test_params = dict(
        source_file_regex=3,
        module="module",
        module_source_file_regex="module-source-file-regex",
        build_variant_regex="!.*",
    )

    response = app_client.post(
        f"/projects/{project}/task-mappings",
        data=json.dumps(test_params),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.get_json()["errors"]["source_file_regex"] == "3 is not of type 'string'"


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_POST_work_item_inserted_with_module_and_no_module_regex(
    get_evg_project_mock, project_task_mapping_work_item_mock, app_client: testing.FlaskClient
):
    project = "valid-evergreen-project"
    get_evg_project_mock.return_value = MagicMock(identifier=project)
    project_task_mapping_work_item_mock.new_task_mappings.return_value.insert.return_value = True
    test_params = dict(source_file_regex="src.*", module="module", build_variant_regex="!.*")

    response = app_client.post(
        f"/projects/{project}/task-mappings",
        data=json.dumps(test_params),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert (
        response.get_json()["custom"]
        == "The module_source_file_regex param is required if a module name is passed in"
    )


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_POST_no_module_passed_in(
    get_evg_project_mock, project_task_mapping_work_item_mock, app_client: testing.FlaskClient
):
    project = "valid-evergreen-project"
    get_evg_project_mock.return_value = MagicMock(identifier=project)
    project_task_mapping_work_item_mock.new_task_mappings.return_value.insert.return_value = True
    test_params = dict(source_file_regex="source-file-regex")

    response = app_client.post(
        f"/projects/{project}/task-mappings",
        data=json.dumps(test_params),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.get_json()["custom"] == f"Work item added for project '{project}'"


@patch(ns("get_evg_project"))
def test_POST_project_not_found(get_evg_project_mock, app_client: testing.FlaskClient):
    get_evg_project_mock.return_value = None
    test_params = dict(source_file_regex="source-file-regex")

    response = app_client.post(
        f"/projects/invalid-evergreen-project/task-mappings",
        data=json.dumps(test_params),
        content_type="application/json",
    )
    assert response.status_code == 404
    assert response.get_json()["custom"] == "Evergreen project not found"


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_POST_project_cannot_be_inserted(
    get_evg_project_mock, project_task_mapping_work_item_mock, app_client: testing.FlaskClient
):
    get_evg_project_mock.return_value = MagicMock()
    project_task_mapping_work_item_mock.new_task_mappings.return_value.insert.return_value = False
    test_params = dict(source_file_regex="source-file-regex")
    project = "project-already-exists-in-work-item-db"

    response = app_client.post(
        f"/projects/{project}/task-mappings",
        data=json.dumps(test_params),
        content_type="application/json",
    )
    assert response.status_code == 422
    assert response.get_json()["custom"] == f"Work item already exists for project '{project}'"
