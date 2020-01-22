"""Controller for test mappings."""
from decimal import Decimal
from typing import List

from evergreen import Project
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from selectedtests.app.models import CustomResponse
from selectedtests.app.parsers import retrieve_evergreen_project, changed_files_parser
from selectedtests.helpers import default_mongo
from selectedtests.test_mappings.get_test_mappings import get_correlated_test_mappings
from selectedtests.work_items.test_mapping_work_item import ProjectTestMappingWorkItem

router = APIRouter()


class TestMappingsWorkItem(BaseModel):
    source_file_regex: str = Field(default=...,
                                   description="""
                                   Regex describing folder containing source files in given project
                                   """)
    test_file_regex: str = Field(default=...,
                                 description="""
                                       Regex describing folder containing test files in given project.
                                       """)
    module: str = Field(default=None, description="Module to include in the analysis")
    module_source_file_regex: str = Field(default=None, description="""
                        Regex describing folder containing source files in given module.
                        Required if module param is provided.
                        """)
    module_test_file_regex: str = Field(default=None, description="""
                        Regex describing folder containing test files in given module.
                        Required if module param is provided.
                        """)


class TestMappingsResponse(BaseModel):
    test_mappings: List = []


@router.get(path="/", response_model=TestMappingsResponse)
def get(threshold: Decimal = 0, project: Project = Depends(retrieve_evergreen_project),
        changed_files: List[str] = Depends(changed_files_parser)) -> TestMappingsResponse:
    """
    Get a list of correlated test mappings for an input list of changed source files.

    :param project: The evergreen project.
    :param changed_files: List of source files to calculate correlated tasks for.
    :param threshold: Minimum threshold desired for flip_count / source_file_seen_count ratio
    """
    test_mappings = get_correlated_test_mappings(
        default_mongo.test_mappings(), changed_files, project.identifier, threshold
    )
    return TestMappingsResponse(test_mappings=test_mappings)


@router.post(path="", response_model=CustomResponse)
def post(work_item_params: TestMappingsWorkItem, project: str) -> CustomResponse:
    """
    Enqueue a project test mapping work item.

    :param work_item_params: The work items to enqueue.
    :param project: The evergreen project identifier.
    """
    module = work_item_params.module
    module_source_file_regex = work_item_params.module_source_file_regex
    module_test_file_regex = work_item_params.module_test_file_regex
    if module and (not module_source_file_regex or not module_test_file_regex):
        raise HTTPException(
            status_code=400,
            detail="The module_source_file_regex and module_test_file_regex params are required if "
                   "a module name is passed in")

    work_item = ProjectTestMappingWorkItem.new_test_mappings(
        project,
        work_item_params.source_file_regex,
        work_item_params.test_file_regex,
        module,
        module_source_file_regex,
        module_test_file_regex,
    )
    if work_item.insert(default_mongo.test_mappings_queue()):
        return CustomResponse(custom=f"Work item added for project '{project}'")
    else:
        raise HTTPException(status_code=422,
                            detail=f"Work item already exists for project '{project}'")
