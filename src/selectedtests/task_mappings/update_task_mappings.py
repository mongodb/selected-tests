"""Methods to update task mappings for a project."""
from typing import Any, Dict, List

import structlog

from evergreen.api import EvergreenApi
from pymongo import UpdateOne

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.helpers import create_query
from selectedtests.project_config import ProjectConfig
from selectedtests.task_mappings.create_task_mappings import generate_task_mappings
from selectedtests.task_mappings.version_limit import VersionLimit

LOGGER = structlog.get_logger()


def update_task_mappings_tasks(
    tasks: List[Dict[str, Any]], source_file: str, mongo: MongoWrapper
) -> None:
    """
    Update task in the task mappings tasks collection.

    :param tasks: A list of tasks.
    :param source_file: The task mappings identifier.
    :param mongo: An instance of MongoWrapper.
    """
    operations = []
    for task in tasks:
        update_test_file = UpdateOne(
            {"source_file": source_file, "name": task["name"], "variant": task["variant"]},
            {"$inc": {"flip_count": task["flip_count"]}},
            upsert=True,
        )
        operations.append(update_test_file)

    result = mongo.task_mappings_tasks().bulk_write(operations)
    LOGGER.debug("bulk_write", result=result.bulk_api_result, source_file=source_file)


def update_task_mappings(mappings: List[Dict], mongo: MongoWrapper) -> None:
    """
    Update task mappings in the task mappings collection.

    :param mappings: A list of test mappings.
    :param mongo: An instance of MongoWrapper.
    """
    for mapping in mappings:
        source_file_seen_count = mapping["source_file_seen_count"]

        query = create_query(mapping, joined=["tasks"], mutable=["source_file_seen_count"])

        result = mongo.task_mappings().update_one(
            query, {"$inc": {"source_file_seen_count": source_file_seen_count}}, upsert=True
        )
        LOGGER.debug(
            "update_one task_mappings",
            result=result.raw_result,
            query=query,
            inc=source_file_seen_count,
        )

        tasks = mapping.get("tasks", [])
        if tasks:
            update_task_mappings_tasks(tasks, mapping["source_file"], mongo)


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

        # TODO: TIG-2375 if generate_task_mappings yielded the mappings in ascending order and
        #  updates were
        #  written in transactions, then this code would be quicker, restartable and error
        #  resistant.
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
