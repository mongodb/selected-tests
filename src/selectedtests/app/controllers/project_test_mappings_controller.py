"""Controller for the health endpoints."""
import json

from flask import jsonify, request
from flask_restplus import abort, Api, fields, Resource, reqparse
from evergreen.api import EvergreenApi

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.evergreen_helper import get_evg_project
from selectedtests.test_mappings.get_mappings import get_correlated_test_mappings
from selectedtests.work_items.project_test_mapping_work_item import ProjectTestMappingWorkItem


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
            "source_file_regex": fields.String(
                description="Regex describing folder containing source files in given project",
                required=True,
            ),
            "test_file_regex": fields.String(
                description="Regex describing folder containing test files in given project.",
                required=True,
            ),
            "module": fields.String(description="Module to include in the analysis"),
            "module_source_file_regex": fields.String(
                description="""
                            Regex describing folder containing source files in given module.
                            Required if module param is provided.
                            """
            ),
            "module_test_file_regex": fields.String(
                description="""
                            Regex describing folder containing test files in given module.
                            Required if module param is provided.
                            """
            ),
        },
    )

    parser = reqparse.RequestParser()
    parser.add_argument(
        "changed_files",
        location="args",
        help="List of source files to calculate correlated tasks for",
        required=True,
    )

    @ns.route("/<project>/test-mappings")
    @api.param("project", "The evergreen project identifier")
    class TestMappings(Resource):
        @ns.response(200, "Success")
        @ns.response(400, "Bad request")
        @ns.response(404, "Evergreen project not found")
        @ns.expect(parser, validate=True)
        def get(self, project: str):
            """
            Get a list of correlated tests for an input list of changed source files.

            :param project: The evergreen project identifier.
            """
            evergreen_project = get_evg_project(evg_api, project)
            if not evergreen_project:
                abort(404, custom="Evergreen project not found")
            else:
                changed_files_string = request.args.get("changed_files")
                if changed_files_string:
                    changed_files = changed_files_string.split(",")
                    test_mappings = get_correlated_test_mappings(
                        mongo.test_mappings(), changed_files, project
                    )
                    return jsonify({"test_mappings": test_mappings})
                else:
                    abort(400, custom="The changed_files query param is required")

        @ns.response(200, "Success")
        @ns.response(400, "Bad request")
        @ns.response(404, "Evergreen project not found")
        @ns.response(422, "Work item already exists for project")
        @ns.expect(test_mappings_work_item, validate=True)
        def post(self, project: str):
            """
            Enqueue a project test mapping work item.

            :param project: The evergreen project identifier.
            """
            evergreen_project = get_evg_project(evg_api, project)
            if not evergreen_project:
                abort(404, custom="Evergreen project not found")
            else:
                work_item_params = json.loads(request.get_data().decode("utf8"))

                module = work_item_params.get("module")
                module_source_file_regex = work_item_params.get("module_source_file_regex")
                if module and not module_source_file_regex:
                    abort(
                        400,
                        custom="The module_source_file_regex param is required if "
                        "a module name is passed in",
                    )
                module_test_file_regex = work_item_params.get("module_test_file_regex")
                if module and not module_test_file_regex:
                    abort(
                        400,
                        custom="The module_test_file_regex param is required if "
                        "a module name is passed in",
                    )

                work_item = ProjectTestMappingWorkItem.new_test_mappings(
                    project,
                    work_item_params.get("source_file_regex"),
                    work_item_params.get("test_file_regex"),
                    module,
                    module_source_file_regex,
                    module_test_file_regex,
                )
                if work_item.insert(mongo.test_mappings_queue()):
                    return jsonify({"custom": f"Work item added for project '{project}'"})
                else:
                    abort(422, custom=f"Work item already exists for project '{project}'")
