"""Controller for the health endpoints."""
import json

from flask import jsonify, request
from flask_restplus import abort, Api, fields, Resource, reqparse
from evergreen.api import EvergreenApi
from decimal import Decimal
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.evergreen_helper import get_evg_project
from selectedtests.task_mappings.get_task_mappings import get_correlated_task_mappings
from selectedtests.work_items.task_mapping_work_item import ProjectTaskMappingWorkItem


def add_project_task_mappings_endpoints(api: Api, mongo: MongoWrapper, evg_api: EvergreenApi):
    """
    Add to the given app instance the task mapping jobs endpoints of the service.

    :param api: An instance of a Flask Restplus Api that wraps a Flask instance
    :param mongo: Mongo Wrapper instance
    :param evg_api: An instance of the evg_api client
    """
    ns = api.namespace("projects", description="Project mappings")

    task_mappings_work_item = ns.model(
        "TaskMappingsWorkItem",
        {
            "source_file_regex": fields.String(
                description="Regex describing folder containing source files in given project",
                required=True,
            ),
            "module": fields.String(description="Module to include in the analysis"),
            "module_source_file_regex": fields.String(
                description="""
                            Regex describing folder containing source files in given module.
                            Required if module param is provided.
                            """
            ),
            "build_variant_regex": fields.String(
                description="Regex that will be used to decide what build variants are analyzed. "
                "Compares to the build variant's display name"
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
    parser.add_argument(
        "threshold",
        type=Decimal,
        location="args",
        help="Minimum threshold desired for flip_count / source_file_seen_count ratio",
    )

    @ns.route("/<project>/task-mappings")
    @api.param("project", "The evergreen project identifier")
    class TaskMappings(Resource):
        @ns.response(200, "Success")
        @ns.response(400, "Bad request")
        @ns.response(404, "Evergreen project not found")
        @ns.expect(parser)
        def get(self, project: str):
            """
            Get a list of correlated task mappings for an input list of changed source files.

            :param project: The evergreen project identifier.
            """
            evergreen_project = get_evg_project(evg_api, project)
            if not evergreen_project:
                abort(404, custom="Evergreen project not found")
            else:
                changed_files_string = request.args.get("changed_files")
                if not changed_files_string:
                    abort(400, custom="Missing changed_files query param")
                else:
                    threshold = request.args.get("threshold", 0)
                    try:
                        threshold = Decimal(threshold)
                    except TypeError:
                        abort(400, custom="Threshold query param must be a decimal")
                    changed_files = changed_files_string.split(",")
                    task_mappings = get_correlated_task_mappings(
                        mongo.task_mappings(), changed_files, project, threshold
                    )
                    return jsonify({"task_mappings": task_mappings})

        @ns.response(200, "Success")
        @ns.response(400, "Bad request")
        @ns.response(404, "Evergreen project not found")
        @ns.response(422, "Work item already exists for project")
        @ns.expect(task_mappings_work_item, validate=True)
        def post(self, project: str):
            """
            Enqueue a project task mapping work item.

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

                work_item = ProjectTaskMappingWorkItem.new_task_mappings(
                    project,
                    work_item_params.get("source_file_regex"),
                    module,
                    module_source_file_regex,
                    work_item_params.get("build_variant_regex"),
                )
                if work_item.insert(mongo.task_mappings_queue()):
                    return jsonify({"custom": f"Work item added for project '{project}'"})
                else:
                    abort(422, custom=f"Work item already exists for project '{project}'")
