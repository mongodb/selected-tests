from flask import testing
import json

from unittest.mock import patch, MagicMock

NS = "selectedtests.app.controllers.project_test_mappings_controller"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


@patch(ns("MONGO_WRAPPER"))
@patch(ns("TestMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_work_item_inserted(
    get_evg_project_mock,
    test_mapping_work_item_mock,
    mongo_wrapper_mock,
    app_client: testing.FlaskClient,
):
    get_evg_project_mock.return_value = MagicMock()
    work_item_mock = MagicMock()
    work_item_mock.insert.return_value = True
    test_mapping_work_item_mock.new_test_mappings.return_value = work_item_mock
    mongo_wrapper_mock.test_mappings_queue.return_value = MagicMock()
    test_params = dict(
        source_file_regex="source-file-regex",
        test_file_regex="test-file-regex",
        module="module",
        module_source_file_regex="module-source-file-regex",
        module_test_file_regex="module-test-file-regex",
    )
    project = "valid-evergreen-project"

    response = app_client.post(f"/projects/{project}/test-mappings", data=json.dumps(test_params))
    assert response.status_code == 200
    assert f"Work item added for '{project}', 'source-file-regex'" in response.get_data(
        as_text=True
    )


@patch(ns("MONGO_WRAPPER"))
@patch(ns("TestMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_no_module_passed_in(
    get_evg_project_mock,
    test_mapping_work_item_mock,
    mongo_wrapper_mock,
    app_client: testing.FlaskClient,
):
    get_evg_project_mock.return_value = MagicMock()
    work_item_mock = MagicMock()
    work_item_mock.insert.return_value = True
    test_mapping_work_item_mock.new_test_mappings.return_value = work_item_mock
    mongo_wrapper_mock.test_mappings_queue.return_value = MagicMock()
    test_params = dict(source_file_regex="source-file-regex", test_file_regex="test-file-regex")
    project = "valid-evergreen-project"

    response = app_client.post(f"/projects/{project}/test-mappings", data=json.dumps(test_params))
    assert response.status_code == 200
    assert f"Work item added for '{project}', 'source-file-regex'" in response.get_data(
        as_text=True
    )


@patch(ns("get_evg_project"))
def test_project_not_found(get_evg_project_mock, app_client: testing.FlaskClient):
    get_evg_project_mock.return_value = None
    test_params = dict(source_file_regex="source-file-regex", test_file_regex="test-file-regex")

    response = app_client.post(
        "/projects/invalid-evergreen-project/test-mappings", data=json.dumps(test_params)
    )
    assert response.status_code == 404
    assert "Evergreen project not found" in response.get_data(as_text=True)


@patch(ns("MONGO_WRAPPER"))
@patch(ns("TestMappingWorkItem"))
@patch(ns("get_evg_project"))
def test_project_cannot_be_inserted(
    get_evg_project_mock,
    test_mapping_work_item_mock,
    mongo_wrapper_mock,
    app_client: testing.FlaskClient,
):
    get_evg_project_mock.return_value = MagicMock()
    work_item_mock = MagicMock()
    work_item_mock.insert.return_value = False
    test_mapping_work_item_mock.new_test_mappings.return_value = work_item_mock
    mongo_wrapper_mock.test_mappings_queue.return_value = MagicMock()
    test_params = dict(source_file_regex="source-file-regex", test_file_regex="test-file-regex")
    project = "project-already-exists-in-work-item-db"

    response = app_client.post(f"/projects/{project}/test-mappings", data=json.dumps(test_params))
    assert response.status_code == 422
    assert f"Work item already exists for '{project}', 'source-file-regex'" in response.get_data(
        as_text=True
    )
