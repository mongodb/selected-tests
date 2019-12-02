"""Functions for processing project test mapping work items."""
import re
import structlog
from typing import Iterable

from datetime import datetime
from typing import Any
from evergreen.api import EvergreenApi
from pymongo import IndexModel, ASCENDING
from pymongo.collection import Collection
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.test_mappings.create_test_mappings import generate_test_mappings
from selectedtests.task_mappings.create_task_mappings import TaskMappings
from selectedtests.work_items.project_test_mapping_work_item import ProjectTestMappingWorkItem
from selectedtests.work_items.project_task_mapping_work_item import ProjectTaskMappingWorkItem

LOGGER = structlog.get_logger()


def setup_indexes(collection: Collection):
    """
    Create appropriate indexes for ProjectTestMappingWorkItems.

    :param collection: Collection to add indexes to.
    """
    index = IndexModel([("project", ASCENDING)], unique=True)
    collection.create_indexes([index])
    LOGGER.info("Adding indexes for collection", collection=collection.name)


def _clear_in_progress_work(collection: Collection):
    """
    Clear the start time of all in progress work items.

    This is done at the start of a run to retry any work items that may not have completed
    during a previous run.

    :param collection: Collection to act on.
    """
    collection.update_many({"end_time": None}, {"$set": {"start_time": None}})


def process_queued_task_mapping_work_items(
    evg_api: EvergreenApi, mongo: MongoWrapper, after_date: datetime
):
    """
    Process task mapping work items that have not yet been processed.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param after_date: The date at which to start analyzing commits of the project.
    """
    _clear_in_progress_work(mongo.task_mappings_queue())
    try:
        for work_item in _generate_task_mapping_work_items(mongo):
            _process_one_task_mapping_work_item(work_item, evg_api, mongo, after_date)
    except:  # noqa: E722
        LOGGER.warning("Unexpected exception processing task mapping work item", exc_info=1)


def _generate_task_mapping_work_items(mongo: MongoWrapper) -> Iterable[ProjectTaskMappingWorkItem]:
    """
    Generate task mapping work items that need to be processed.

    :param mongo: Mongo db containing work item queue.
    :return: Iterator over task mapping work items.
    """
    work_item = ProjectTaskMappingWorkItem.next(mongo.task_mappings_queue())
    while work_item:
        yield work_item
        work_item = ProjectTaskMappingWorkItem.next(mongo.task_mappings_queue())


def _process_one_task_mapping_work_item(
    work_item: ProjectTaskMappingWorkItem,
    evg_api: EvergreenApi,
    mongo: MongoWrapper,
    after_date: datetime,
):
    """
    Process a task mapping work item.

    :param work_item: Task mapping to create.
    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param after_date: The date at which to start analyzing commits of the project.
    """
    log = LOGGER.bind(project=work_item.project, module=work_item.module)
    log.info("Starting task mapping work item processing for work_item")
    if _run_create_task_mappings(evg_api, mongo, work_item, after_date, log):
        work_item.complete(mongo.task_mappings_queue())


def _run_create_task_mappings(
    evg_api: EvergreenApi,
    mongo: MongoWrapper,
    work_item: ProjectTaskMappingWorkItem,
    after_date: datetime,
    log: Any,
) -> bool:
    """
    Generate task mappings for a given work item.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param work_item: An instance of ProjectTestMappingWorkItem.
    :param after_date: The date at which to start analyzing commits of the project.
    """
    source_re = re.compile(work_item.source_file_regex)
    module_source_re = None
    if work_item.module:
        module_source_re = re.compile(work_item.module_source_file_regex)

    mappings = TaskMappings.create_task_mappings(
        evg_api,
        work_item.project,
        after_date,
        source_re,
        module_name=work_item.module,
        module_file_regex=module_source_re,
        build_regex=work_item.build_variant_regex,
    )
    transformed_mappings = mappings.transform()
    if transformed_mappings:
        mongo.task_mappings().insert_many(transformed_mappings)
    log.info("Finished task mapping work item processing")

    return True


def process_queued_test_mapping_work_items(
    evg_api: EvergreenApi, mongo: MongoWrapper, after_date: datetime
):
    """
    Process test mapping work items that have not yet been processed.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param after_date: The date at which to start analyzing commits of the project.
    """
    _clear_in_progress_work(mongo.test_mappings_queue())
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
    Generate task mappings for a given work item.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param work_item: An instance of ProjectTestMappingWorkItem.
    :param after_date: The date at which to start analyzing commits of the project.
    """
    source_re = re.compile(work_item.source_file_regex)
    test_re = re.compile(work_item.test_file_regex)
    module_source_re = None
    module_test_re = None
    if work_item.module:
        module_source_re = re.compile(work_item.module_source_file_regex)
        module_test_re = re.compile(work_item.module_test_file_regex)

    test_mappings_list = generate_test_mappings(
        evg_api,
        work_item.project,
        source_re,
        test_re,
        after_date,
        module_name=work_item.module,
        module_source_re=module_source_re,
        module_test_re=module_test_re,
    )
    if test_mappings_list:
        mongo.test_mappings().insert_many(test_mappings_list)
    log.info("Finished test mapping work item processing")

    return True
