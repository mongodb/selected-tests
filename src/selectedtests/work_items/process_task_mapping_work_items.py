"""Functions for processing project task mapping work items."""
from datetime import datetime
from typing import Any, Iterable

import structlog

from evergreen.api import EvergreenApi
from structlog.threadlocal import tmp_bind

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.project_config import ProjectConfig
from selectedtests.task_mappings.create_task_mappings import generate_task_mappings
from selectedtests.task_mappings.update_task_mappings import update_task_mappings
from selectedtests.task_mappings.version_limit import VersionLimit
from selectedtests.work_items.process_test_mapping_work_items import clear_in_progress_work
from selectedtests.work_items.task_mapping_work_item import ProjectTaskMappingWorkItem

LOGGER = structlog.get_logger()


def process_queued_task_mapping_work_items(
    evg_api: EvergreenApi, mongo: MongoWrapper, after_date: datetime
) -> None:
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
) -> None:
    """
    Process a task mapping work item.

    :param work_item: Task mapping to create.
    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    :param after_date: The date at which to start analyzing commits of the project.
    """
    with tmp_bind(LOGGER, project=work_item.project, evergreen_module=work_item.module) as log:
        log.info("Starting task mapping work item processing for work_item")
        if _seed_task_mappings_for_project(evg_api, mongo, work_item, after_date, log):
            work_item.complete(mongo.task_mappings_queue())


def _seed_task_mappings_for_project(
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
    # TODO: if generate_task_mappings yielded the mappings in ascending order and updates were
    #  written in transactions, then this code would be quicker, restartable and error
    #  resistant.
    mappings, most_recent_version_analyzed = generate_task_mappings(
        evg_api,
        work_item.project,
        VersionLimit(stop_at_date=after_date),
        work_item.source_file_regex,
        module_name=work_item.module,
        module_source_file_pattern=work_item.module_source_file_regex,
        build_variant_pattern=work_item.build_variant_regex,
    )

    project_config = ProjectConfig.get(mongo.project_config(), work_item.project)
    project_config.task_config.update(
        most_recent_version_analyzed,
        work_item.source_file_regex,
        work_item.build_variant_regex,
        work_item.module,
        work_item.module_source_file_regex,
    )

    project_config.save(mongo.project_config())

    if mappings:
        update_task_mappings(mappings, mongo)
    else:
        LOGGER.info("No task mappings generated")
    log.info("Finished task mapping work item processing")

    return True
