"""Functions for processing project task mapping work items."""
import structlog

from datetime import datetime
from evergreen.api import EvergreenApi
from typing import Iterable, Any

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.task_mappings.create_task_mappings import generate_task_mappings
from selectedtests.work_items.process_test_mapping_work_items import clear_in_progress_work
from selectedtests.work_items.task_mapping_work_item import ProjectTaskMappingWorkItem
from selectedtests.task_mappings.version_limit import VersionLimit

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
    if _seed_task_mappings_for_project(evg_api, mongo, work_item, after_date, log):
        work_item.complete(mongo.task_mappings_queue())


def _create_project_in_task_mappings_config(mongo, work_item, most_recent_version_analyzed):
    mongo.task_mappings_project_config().insert_one(
        {
            "project": work_item.project,
            "most_recent_version_analyzed": most_recent_version_analyzed,
            "source_re": work_item.source_file_regex,
            "build_re": work_item.build_variant_regex,
            "module": work_item.module,
            "module_source_re": work_item.module_source_file_regex,
        }
    )


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
    mappings, most_recent_version_analyzed = generate_task_mappings(
        evg_api,
        work_item.project,
        VersionLimit(stop_at_date=after_date),
        work_item.source_file_regex,
        module_name=work_item.module,
        module_source_file_regex=work_item.module_source_file_regex,
        build_variant_regex=work_item.build_variant_regex,
    )
    _create_project_in_task_mappings_config(mongo, work_item, most_recent_version_analyzed)
    if mappings:
        mongo.task_mappings().insert_many(mappings)
    else:
        LOGGER.info("No task mappings generated")
    log.info("Finished task mapping work item processing")

    return True


def _update_task_mappings_config(mongo, project, most_recent_version_analyzed):
    mongo.task_mappings_project_config().update_one(
        {"project": project},
        {"$set": {"most_recent_version_analyzed": most_recent_version_analyzed}},
    )


def update_task_mappings_since_last_commit(evg_api: EvergreenApi, mongo: MongoWrapper):
    """
    Update task mappings that are being tracked in the task mappings project config collection.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    """
    LOGGER.info("Updating task mappings")
    project_cursor = mongo.task_mappings_project_config().find({})
    for project_config in project_cursor:
        LOGGER.info("Updating task mappings for project", project_config=project_config)
        mappings, most_recent_version_analyzed = generate_task_mappings(
            evg_api,
            project_config["project"],
            VersionLimit(stop_at_version_id=project_config["most_recent_version_analyzed"]),
            project_config["source_re"],
            module_name=project_config["module"],
            module_source_file_regex=project_config["module_source_re"],
            build_variant_regex=project_config["build_re"],
        )

        _update_task_mappings_config(mongo, project_config["project"], most_recent_version_analyzed)
        if mappings:
            mongo.task_mappings().insert_many(mappings)
        else:
            LOGGER.info("No task mappings generated")
    LOGGER.info("Finished task mapping updating")
