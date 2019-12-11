"""Functions for processing project test mapping work items."""
from datetime import datetime
from typing import Any, Iterable
import re
import structlog

from evergreen.api import EvergreenApi
from pymongo.collection import Collection
from tempfile import TemporaryDirectory

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.evergreen_helper import get_module_commit_on_date, get_project_commit_on_date
from selectedtests.test_mappings.create_test_mappings import generate_test_mappings
from selectedtests.work_items.test_mapping_work_item import ProjectTestMappingWorkItem

LOGGER = structlog.get_logger()


def clear_in_progress_work(collection: Collection):
    """
    Clear the start time of all in progress work items.

    This is done at the start of a run to retry any work items that may not have completed
    during a previous run.

    :param collection: Collection to act on.
    """
    collection.update_many({"end_time": None}, {"$set": {"start_time": None}})


def process_queued_test_mapping_work_items(
    evg_api: EvergreenApi, mongo: MongoWrapper, after_date: datetime
):
    """
    Process test mapping work items that have not yet been processed.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param after_date: The date at which to start analyzing commits of the project.
    """
    clear_in_progress_work(mongo.test_mappings_queue())
    try:
        for work_item in _generate_test_mapping_work_items(mongo):
            _process_one_test_mapping_work_item(work_item, evg_api, mongo, after_date)
    except:  # noqa: E722
        LOGGER.warning("Unexpected exception processing test mapping work item", exc_info=1)


def _generate_test_mapping_work_items(mongo: MongoWrapper) -> Iterable[ProjectTestMappingWorkItem]:
    """
    Generate test mapping work items that need to be processed.

    :param mongo: Mongo db containing work item queue.
    :return: Iterator over test mapping work items.
    """
    work_item = ProjectTestMappingWorkItem.next(mongo.test_mappings_queue())
    while work_item:
        yield work_item
        work_item = ProjectTestMappingWorkItem.next(mongo.test_mappings_queue())


def _process_one_test_mapping_work_item(
    work_item: ProjectTestMappingWorkItem,
    evg_api: EvergreenApi,
    mongo: MongoWrapper,
    after_date: datetime,
):
    """
    Process a test mapping work item.

    :param work_item: Test mapping to create.
    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param after_date: The date at which to start analyzing commits of the project.
    :return: Whether all work items have been processed.
    """
    log = LOGGER.bind(project=work_item.project, module=work_item.module)
    log.info("Starting test mapping work item processing for work_item")
    if _run_create_test_mappings(evg_api, mongo, work_item, after_date, log):
        work_item.complete(mongo.test_mappings_queue())


def _run_create_test_mappings(
    evg_api: EvergreenApi,
    mongo: MongoWrapper,
    work_item: ProjectTestMappingWorkItem,
    after_date: datetime,
    log: Any,
) -> bool:
    """
    Generate test mappings for a given work item.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param work_item: An instance of ProjectTestMappingWorkItem.
    :param after_date: The date at which to start analyzing commits of the project.
    """
    with TemporaryDirectory() as temp_dir:
        after_project_commit = get_project_commit_on_date(
            temp_dir, evg_api, work_item.project, after_date
        )
    source_re = re.compile(work_item.source_file_regex)
    test_re = re.compile(work_item.test_file_regex)
    after_module_commit = None
    module_source_re = None
    module_test_re = None
    if work_item.module:
        with TemporaryDirectory() as temp_dir:
            after_module_commit = get_module_commit_on_date(
                temp_dir, evg_api, work_item.project, work_item.module, after_date
            )
        module_source_re = re.compile(work_item.module_source_file_regex)
        module_test_re = re.compile(work_item.module_test_file_regex)

    test_mappings_result = generate_test_mappings(
        evg_api,
        work_item.project,
        after_project_commit,
        source_re,
        test_re,
        module_name=work_item.module,
        after_module_commit=after_module_commit,
        module_source_re=module_source_re,
        module_test_re=module_test_re,
    )
    if test_mappings_result.test_mappings_list:
        mongo.test_mappings().insert_many(test_mappings_result.test_mappings_list)
    else:
        log.info("No test mappings generated")
    log.info("Finished test mapping work item processing")

    return True
