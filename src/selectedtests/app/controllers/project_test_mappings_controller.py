"""Controller for test mappings."""
from decimal import Decimal
from typing import List

import structlog

from evergreen import EvergreenApi
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from selectedtests.app.dependencies import get_db, get_evg
from selectedtests.app.evergreen import try_retrieve_evergreen_project
from selectedtests.app.models import CustomResponse
from selectedtests.app.parsers import parse_changed_files
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.test_mappings.get_test_mappings import get_correlated_test_mappings
from selectedtests.work_items.test_mapping_work_item import ProjectTestMappingWorkItem

LOGGER = structlog.get_logger(__name__)
router = APIRouter()


class TestMappingsWorkItem(BaseModel):
    """Test mappings work item model."""

    source_file_regex: str = Field(
        default=..., description="Regex describing folder containing source files in given project"
    )
    test_file_regex: str = Field(
        default=..., description="Regex describing folder containing test files in given project."
    )
    module: str = Field(default=None, description="Module to include in the analysis")
    module_source_file_regex: str = Field(
        default=None,
        description="Regex describing folder containing source files in given module."
        "Required if module param is provided.",
    )
    module_test_file_regex: str = Field(
        default=None,
        description="Regex describing folder containing test files in given module."
        "Required if module param is provided.",
    )


class TestMappingsResponse(BaseModel):
    """Model for test mapping responses."""

    test_mappings: List = []


@router.get(
    path="",
    response_model=TestMappingsResponse,
    responses={
        200: {"description": "Success", "model": TestMappingsWorkItem},
        400: {"description": "Bad Request"},
        404: {"description": "Evergreen project not found"},
    },
)
def get(
    project: str,
    changed_files: str,
    threshold: Decimal = Decimal(0),
    evg_api: EvergreenApi = Depends(get_evg),
    db: MongoWrapper = Depends(get_db),
) -> TestMappingsResponse:
    """
    Get a list of correlated test mappings for an input list of changed source files.

    :param evg_api: The evergreen API.
    :param db: The database.
    :param project: The evergreen project.
    :param changed_files: List of source files to calculate correlated tasks for.
    :param threshold: Minimum threshold desired for flip_count / source_file_seen_count ratio
    """
    LOGGER.info("Starting fetching test_mappings for project", project=project)
    evg_project = try_retrieve_evergreen_project(project, evg_api)
    LOGGER.info("Retrieved evergreen project information", evergreen_project=evg_project.identifier)
    test_mappings = get_correlated_test_mappings(
        db.test_mappings(), parse_changed_files(changed_files), evg_project.identifier, threshold
    )
    return TestMappingsResponse(test_mappings=test_mappings)


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
    work_item_params: TestMappingsWorkItem,
    project: str,
    evg_api: EvergreenApi = Depends(get_evg),
    db: MongoWrapper = Depends(get_db),
) -> CustomResponse:
    """
    Enqueue a project test mapping work item.

    :param evg_api: Evergreen API.
    :param db: The database
    :param work_item_params: The work items to enqueue.
    :param project: The evergreen project.
    """
    LOGGER.info("Adding a test mapping work item to queue for project", project=project)
    evg_project = try_retrieve_evergreen_project(project, evg_api)
    module = work_item_params.module
    module_source_file_regex = work_item_params.module_source_file_regex
    module_test_file_regex = work_item_params.module_test_file_regex
    if module and (not module_source_file_regex or not module_test_file_regex):
        raise HTTPException(
            status_code=400,
            detail="The module_source_file_regex and module_test_file_regex"
            " params are required if a module name is passed in",
        )

    work_item = ProjectTestMappingWorkItem.new_test_mappings(
        evg_project.identifier,
        work_item_params.source_file_regex,
        work_item_params.test_file_regex,
        module,
        module_source_file_regex,
        module_test_file_regex,
    )
    if work_item.insert(db.test_mappings_queue()):
        return CustomResponse(custom=f"Work item added for project '{evg_project.identifier}'")
    else:
        raise HTTPException(
            status_code=422,
            detail=f"Work item already exists for project '{evg_project.identifier}'",
        )
