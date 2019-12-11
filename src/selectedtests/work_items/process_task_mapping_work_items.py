"""Functions for processing project task mapping work items."""
import structlog
import re

from datetime import datetime
from evergreen.api import EvergreenApi
from typing import Iterable, Any

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.evergreen_helper import get_version_on_date
from selectedtests.task_mappings.create_task_mappings import TaskMappings
from selectedtests.work_items.process_test_mapping_work_items import clear_in_progress_work
from selectedtests.work_items.task_mapping_work_item import ProjectTaskMappingWorkItem

LOGGER = structlog.get_logger()


def process_queued_task_mapping_work_items(
    evg_api: EvergreenApi, mongo: MongoWrapper, after_date: datetime
):
    """
    Process task mapping work items that have not yet been processed.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param after_date: The date at which to start analyzing commits of the project.
    """
    clear_in_progress_work(mongo.task_mappings_queue())
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
    after_version = get_version_on_date(evg_api, work_item.project, after_date)
    source_re = re.compile(work_item.source_file_regex)
    module_source_re = None
    if work_item.module:
        module_source_re = re.compile(work_item.module_source_file_regex)

    mappings, most_recent_version_analyzed = TaskMappings.create_task_mappings(
        evg_api,
        work_item.project,
        after_version,
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
