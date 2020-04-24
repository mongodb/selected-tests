"""Controller for task mappings."""
from decimal import Decimal
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from selectedtests.app.evergreen import try_retrieve_evergreen_project
from selectedtests.app.models import CustomResponse
from selectedtests.app.parsers import parse_changed_files
from selectedtests.task_mappings.get_task_mappings import get_correlated_task_mappings
from selectedtests.work_items.task_mapping_work_item import ProjectTaskMappingWorkItem

router = APIRouter()


class TaskMappingsWorkItem(BaseModel):
    """Task mappings work item model."""

    source_file_regex: str = Field(
        default=..., description="Regex describing folder containing source files in given project"
    )
    module: str = Field(default=None, description="Module to include in the analysis")
    module_source_file_regex: str = Field(
        default=None,
        description="Regex describing folder containing source files in given module."
        "Required if module param is provided.",
    )
    build_variant_regex: str = Field(
        default=None,
        description="Regex that will be used to decide what build variants are analyzed."
        "Compares to the build variant's display name.",
    )


class TaskMappingsResponse(BaseModel):
    """Model for task mapping responses."""

    task_mappings: List = []


@router.get(
    path="",
    response_model=TaskMappingsResponse,
    responses={
        200: {"description": "Success", "model": TaskMappingsResponse},
        400: {"description": "Bad Request"},
        404: {"description": "Evergreen project not found"},
    },
)
def get(
    changed_files: str,
    project: str,
    threshold: Decimal = Decimal(0),
) -> TaskMappingsResponse:
    """
    Get a list of correlated task mappings for an input list of changed source files.

    :param project: The evergreen project.
    :param changed_files: List of source files to calculate correlated tasks for.
    :param threshold: Minimum threshold desired for flip_count / source_file_seen_count ratio
    """
    evg_project = try_retrieve_evergreen_project(project)
    task_mappings = get_correlated_task_mappings(
        parse_changed_files(changed_files), evg_project.identifier, threshold
    )
    return TaskMappingsResponse(task_mappings=task_mappings)


@router.post(
    path="",
    response_model=CustomResponse,
    responses={
        200: {"description": "Success", "model": CustomResponse},
        400: {"description": "Bad Request"},
        404: {"description": "Evergreen project not found"},
        422: {"description": "Work item already exists for project"},
    },
)
def post(
    work_item_params: TaskMappingsWorkItem,
    project: str,
) -> CustomResponse:
    """
    Enqueue a project task mapping work item.

    :param work_item_params: The work items to enqueue.
    :param project: The evergreen project identifier.
    """
    evg_project = try_retrieve_evergreen_project(project)
    module = work_item_params.module
    module_source_file_regex = work_item_params.module_source_file_regex
    if module and not module_source_file_regex:
        raise HTTPException(
            status_code=400,
            detail="The module_source_file_regex param is required if "
            "a module name is passed in",
        )

    work_item = ProjectTaskMappingWorkItem.new_task_mappings(
        evg_project.identifier,
        work_item_params.source_file_regex,
        module,
        module_source_file_regex,
        work_item_params.build_variant_regex,
    )

    if work_item.insert():
        return CustomResponse(custom=f"Work item added for project '{evg_project.identifier}'")
    else:
        raise HTTPException(
            status_code=422,
            detail=f"Work item already exists for project '{evg_project.identifier}'",
        )
