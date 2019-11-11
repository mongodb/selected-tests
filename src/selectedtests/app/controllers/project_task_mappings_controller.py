"""Controller for the health endpoints."""
import json

from flask import jsonify, request
from flask_restplus import abort, Api, fields, Resource
from evergreen.api import EvergreenApi

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.work_items.project_task_mapping_work_item import ProjectTaskMappingWorkItem
from selectedtests.evergreen_helper import get_evg_project


def add_project_task_mappings_endpoints(api: Api, mongo: MongoWrapper, evg_api: EvergreenApi):
    """
    Add to the given app instance the task mapping jobs endpoints of the service.

    :param api: An instance of a Flask Restplus Api that wraps a Flask instance
    :param mongo: Mongo Wrapper instance
    :param evg_api: An instance of the evg_api client
    """
    ns = api.namespace("projects", description="Project task mappings")

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

    response_body = ns.model(
        "TaskMappingsResponseBody",
        {"custom": fields.String(description="Message describing the result of the request")},
    )

    @ns.route("/<project>/task-mappings")
    @api.param("project", "The evergreen project identifier")
    class TaskMappingsWorkItem(Resource):
        @ns.response(200, "Success", response_body)
        @ns.response(400, "Bad request", response_body)
        @ns.response(404, "Evergreen project not found", response_body)
        @ns.response(422, "Work item already exists for project", response_body)
        @ns.expect(task_mappings_work_item, validate=True)
        def post(self, project: str):
            """
            Enqueue a project task mapping work item.

            :param project: The name of an evergreen project.
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
