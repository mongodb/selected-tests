from flask import testing
import json
import re

from unittest.mock import patch, MagicMock

NS = "selectedtests.app.controllers.project_task_mappings_controller"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_work_item_inserted(
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
    assert f"Work item added for project '{project}'" in response.get_data(as_text=True)


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_work_item_inserted_with_incorrect_params(
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
    assert re.match(
        "^.*source_file_regex.* is not of type.*string", response.get_data(as_text=True)
    )


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_work_item_inserted_with_module_and_no_module_regex(
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
    assert re.match(
        "^.*module_source_file_regex param is required if a module name is passed in",
        response.get_data(as_text=True),
    )


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_no_module_passed_in(
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
    assert f"Work item added for project '{project}'" in response.get_data(as_text=True)


@patch(ns("get_evg_project"))
def test_project_not_found(get_evg_project_mock, app_client: testing.FlaskClient):
    get_evg_project_mock.return_value = None
    test_params = dict(source_file_regex="source-file-regex")

    response = app_client.post(
        f"/projects/invalid-evergreen-project/task-mappings",
        data=json.dumps(test_params),
        content_type="application/json",
    )
    assert response.status_code == 404
    assert "Evergreen project not found" in response.get_data(as_text=True)


@patch(ns("ProjectTaskMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_project_cannot_be_inserted(
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
    assert f"Work item already exists for project '{project}'" in response.get_data(as_text=True)