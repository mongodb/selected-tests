"""Controller for the health endpoints."""
import json

from flask import jsonify, request
from flask_restplus import abort, Api, fields, Resource
from evergreen.api import EvergreenApi

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.app.test_mapping_work_item import TestMappingWorkItem
from selectedtests.evergreen_helper import get_evg_project


def add_project_test_mappings_endpoints(api: Api, mongo: MongoWrapper, evg_api: EvergreenApi):
    """
    Add to the given app instance the test mapping jobs endpoints of the service.

    :param api: An instance of a Flask Restplus Api that wraps a Flask instance
    :param mongo: Mongo Wrapper instance
    :param evg_api: An instance of the evg_api client
    """
    ns = api.namespace("projects", description="Project Test Mappings")

    test_mappings_work_item = ns.model(
        "TestMappingsWorkItem",
        {
            "project": fields.String(description="The evergreen project identifier", required=True),
            "source_file_regex": fields.String(
                description="Regex describing folder containing source files in given project",
                required=True,
            ),
            "test_file_regex": fields.String(
                description="Regex describing folder containing test files in given project.",
                required=True,
            ),
            "module": fields.String(description="Module to include in the analysis", required=True),
            "module_source_file_regex": fields.String(
                description="Regex describing folder containing source files in given module",
                required=True,
            ),
            "module_test_file_regex": fields.String(
                description="Regex describing folder containing test files in given module",
                required=True,
            ),
        },
    )

    @ns.route("/<project>/test-mappings")
    @api.param("project", "The evergreen project identifier")
    class TestMappingsWorkItem(Resource):
        @ns.response(200, "Success", test_mappings_work_item)
        @ns.response(404, "Evergreen project not found", test_mappings_work_item)
        @ns.response(422, "Work item already exists for project", test_mappings_work_item)
        @ns.expect(test_mappings_work_item)
        def post(self, project):
            """Enqueue a project test mapping work item."""
            evergreen_project = get_evg_project(evg_api, project)
            if not evergreen_project:
                abort(404, custom="Evergreen project not found")
            else:
                work_item_params = json.loads(request.get_data().decode("utf8"))

                source_file_regex = work_item_params.get("source_file_regex")
                work_item = TestMappingWorkItem.new_test_mappings(
                    project,
                    source_file_regex,
                    work_item_params.get("test_file_regex"),
                    work_item_params.get("module"),
                    work_item_params.get("module_source_file_regex"),
                    work_item_params.get("module_test_file_regex"),
                )
                if work_item.insert(mongo.test_mappings_queue()):
                    return jsonify({f"Work item added for project '{project}'": True})
                else:
                    abort(422, custom=f"Work item already exists for project '{project}'")
