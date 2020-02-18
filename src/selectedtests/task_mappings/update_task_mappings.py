"""Methods to update task mappings for a project."""
from typing import Any, Dict, List

import structlog

from evergreen.api import EvergreenApi
from pymongo import ReturnDocument, UpdateOne
from pymongo.errors import BulkWriteError

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.helpers import create_query
from selectedtests.project_config import ProjectConfig
from selectedtests.task_mappings.create_task_mappings import generate_task_mappings
from selectedtests.task_mappings.version_limit import VersionLimit

LOGGER = structlog.get_logger()


def update_task_mappings_tasks(
    tasks: List[Dict[str, Any]], task_mapping_id: Dict[str, Any], mongo: MongoWrapper
) -> None:
    """
    Update task in the task mappings tasks collection.

    :param tasks: A list of tasks.
    :param task_mapping_id: The containing task_mapping identifier.
    :param mongo: An instance of MongoWrapper.
    """
    operations = []
    for task in tasks:
        query = create_query(task, mutable=["flip_count"])
        query = dict(**query, **task_mapping_id)

        update_test_file = UpdateOne(
            query, {"$inc": {"flip_count": task["flip_count"]}}, upsert=True
        )
        operations.append(update_test_file)

    try:
        result = mongo.task_mappings_tasks().bulk_write(operations)
        LOGGER.debug("bulk_write", result=result.bulk_api_result, parent=task_mapping_id)
    except BulkWriteError as bwe:
        # bulk write error default message is not always that helpful, so dump the details here.
        LOGGER.exception(
            "bulk_write error", parent=task_mapping_id, operations=operations, details=bwe.details
        )
        raise


def update_task_mappings(mappings: List[Dict], mongo: MongoWrapper) -> None:
    """
    Update task mappings in the task mappings collection.

    :param mappings: A list of test mappings.
    :param mongo: An instance of MongoWrapper.
    """
    for mapping in mappings:
        source_file_seen_count = mapping["source_file_seen_count"]

        query = create_query(mapping, joined=["tasks"], mutable=["source_file_seen_count"])

        task_mapping = mongo.task_mappings().find_one_and_update(
            query,
            {"$inc": {"source_file_seen_count": source_file_seen_count}},
            projection={"_id": 1},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        LOGGER.debug(
            "update_one task_mappings",
            task_mapping=task_mapping,
            query=query,
            inc=source_file_seen_count,
        )

        tasks = mapping.get("tasks", [])
        if tasks:
            task_mapping_id = {"task_mapping_id": task_mapping["_id"]}
            update_task_mappings_tasks(tasks, task_mapping_id, mongo)


def update_task_mappings_since_last_commit(evg_api: EvergreenApi, mongo: MongoWrapper) -> None:
    """
    Update task mappings that are being tracked in the task mappings project config collection.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    """
    LOGGER.info("Updating task mappings")
    project_cursor = mongo.project_config().find({})
    for project_config in project_cursor:
        LOGGER.info("Updating task mappings for project", project_config=project_config)
        task_config = project_config["task_config"]

        mappings, most_recent_version_analyzed = generate_task_mappings(
            evg_api,
            project_config["project"],
            VersionLimit(stop_at_version_id=task_config["most_recent_version_analyzed"]),
            task_config["source_file_regex"],
            module_name=task_config["module"],
            module_source_file_pattern=task_config["module_source_file_regex"],
            build_variant_pattern=task_config["build_variant_regex"],
        )

        project_config = ProjectConfig.get(mongo.project_config(), project_config["project"])
        project_config.task_config.update_most_recent_version_analyzed(most_recent_version_analyzed)
        project_config.save(mongo.project_config())

        if mappings:
            update_task_mappings(mappings, mongo)
        else:
            LOGGER.info("No task mappings generated")
    LOGGER.info("Finished task mapping updating")
