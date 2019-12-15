"""Functions for processing project test mapping work items."""
from datetime import datetime
from typing import Any, Iterable
import structlog

from evergreen.api import EvergreenApi
from pymongo.collection import Collection

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.test_mappings.commit_limit import CommitLimit
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
    if _seed_test_mappings_for_project(evg_api, mongo, work_item, after_date, log):
        work_item.complete(mongo.test_mappings_queue())


def _create_project_in_test_mappings_config(mongo, work_item, test_mappings_result):
    result = test_mappings_result
    mongo.test_mappings_project_config().insert_one(
        {
            "project": work_item.project,
            "most_recent_project_commit_analyzed": result.most_recent_project_commit_analyzed,
            "source_re": work_item.source_file_regex,
            "test_re": work_item.test_file_regex,
            "module": work_item.module,
            "most_recent_module_commit_analyzed": result.most_recent_module_commit_analyzed,
            "module_source_re": work_item.module_source_file_regex,
            "module_test_re": work_item.module_test_file_regex,
        }
    )


def _seed_test_mappings_for_project(
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
    test_mappings_result = generate_test_mappings(
        evg_api,
        work_item.project,
        CommitLimit(stop_at_date=after_date),
        work_item.source_file_regex,
        work_item.test_file_regex,
        module_name=work_item.module,
        module_commit_limit=CommitLimit(stop_at_date=after_date),
        module_source_file_regex=work_item.module_source_file_regex,
        module_test_file_regex=work_item.module_test_file_regex,
    )
    _create_project_in_test_mappings_config(mongo, work_item, test_mappings_result)
    if test_mappings_result.test_mappings_list:
        mongo.test_mappings().insert_many(test_mappings_result.test_mappings_list)
    else:
        log.info("No test mappings generated")
    log.info("Finished test mapping work item processing")

    return True


def _update_test_mappings_config(mongo, project, test_mappings_result):
    result = test_mappings_result
    mongo.test_mappings_project_config().update_one(
        {"project": project},
        {
            "$set": {
                "most_recent_project_commit_analyzed": result.most_recent_project_commit_analyzed,
                "most_recent_module_commit_analyzed": result.most_recent_module_commit_analyzed,
            }
        },
    )


def update_test_mappings_since_last_commit(evg_api: EvergreenApi, mongo: MongoWrapper):
    """
    Update test mappings that are being tracked in the test mappings project config collection.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    """
    LOGGER.info("Updating test mappings")
    project_cursor = mongo.test_mappings_project_config().find({})
    for project_config in project_cursor:
        LOGGER.info("Updating test mappings for project", project_config=project_config)
        test_mappings_result = generate_test_mappings(
            evg_api,
            project_config["project"],
            CommitLimit(stop_at_commit_sha=project_config["most_recent_project_commit_analyzed"]),
            project_config["source_re"],
            project_config["test_re"],
            module_name=project_config["module"],
            module_commit_limit=CommitLimit(
                stop_at_commit_sha=project_config["most_recent_module_commit_analyzed"]
            ),
            module_source_file_regex=project_config["module_source_re"],
            module_test_file_regex=project_config["module_source_re"],
        )
        _update_test_mappings_config(mongo, project_config["project"], test_mappings_result)
        if test_mappings_result.test_mappings_list:
            mongo.test_mappings().insert_many(test_mappings_result.test_mappings_list)
        else:
            LOGGER.info("No test mappings generated")
    LOGGER.info("Finished test mapping updating")
