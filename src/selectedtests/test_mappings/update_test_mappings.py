"""Methods to update test mappings for a project."""
from typing import Any, Dict, List

import structlog

from evergreen.api import EvergreenApi
from pymongo import ReturnDocument, UpdateOne
from pymongo.errors import BulkWriteError

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.helpers import create_query
from selectedtests.project_config import ProjectConfig
from selectedtests.test_mappings.commit_limit import CommitLimit
from selectedtests.test_mappings.create_test_mappings import generate_test_mappings

LOGGER = structlog.get_logger()


def update_test_mappings_test_files(
    test_files: List[Dict[str, Any]], test_mapping_id: Dict[str, Any], mongo: MongoWrapper
) -> None:
    """
    Update test_files in the test mappings test_files project config collection.

    :param test_files: A list of test mappings.
    :param test_mapping_id: The containing test_mappings identifier.
    :param mongo: An instance of MongoWrapper.
    """
    operations = []
    for test_file in test_files:
        query = create_query(test_file, mutable=["test_file_seen_count"])
        query = dict(**query, **test_mapping_id)

        update_test_file = UpdateOne(
            query,
            {"$inc": {"test_file_seen_count": test_file["test_file_seen_count"]}},
            upsert=True,
        )
        operations.append(update_test_file)

    try:
        result = mongo.test_mappings_test_files().bulk_write(operations)
        LOGGER.debug("bulk_write", result=result.bulk_api_result, parent=test_mapping_id)
    except BulkWriteError as bwe:
        # bulk write error default message is not always that helpful, so dump the details here.
        LOGGER.exception(
            "bulk_write error", parent=test_mapping_id, operations=operations, details=bwe.details
        )
        raise


def update_test_mappings(test_mappings: List[Dict[str, Any]], mongo: MongoWrapper) -> None:
    """
    Update test mappings in the test mappings collection.

    :param test_mappings: A list of test mappings.
    :param mongo: An instance of MongoWrapper.
    """
    for mapping in test_mappings:
        source_file_seen_count = mapping["source_file_seen_count"]

        query = create_query(mapping, joined=["test_files"], mutable=["source_file_seen_count"])

        test_mapping = mongo.test_mappings().find_one_and_update(
            query,
            {"$inc": {"source_file_seen_count": source_file_seen_count}},
            projection={"_id": 1},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        LOGGER.debug(
            "update_one test_mappings",
            test_mapping=test_mapping,
            query=query,
            inc=source_file_seen_count,
        )

        test_files = mapping.get("test_files", [])
        if test_files:
            test_mapping_id = {"test_mapping_id": test_mapping["_id"]}
            update_test_mappings_test_files(test_files, test_mapping_id, mongo)


def update_test_mappings_since_last_commit(evg_api: EvergreenApi, mongo: MongoWrapper) -> None:
    """
    Update test mappings that are being tracked in the test mappings project config collection.

    :param evg_api: An instance of the evg_api client
    :param mongo: An instance of MongoWrapper.
    """
    LOGGER.info("Updating test mappings")
    project_cursor = mongo.project_config().find({})
    for project_config in project_cursor:
        LOGGER.info("Updating test mappings for project", project_config=project_config)
        test_config = project_config["test_config"]

        # TODO: TIG-2375 if generate_test_mappings yielded the mappings in ascending order and
        #  updates were written in transactions, then this code would be quicker, restartable and
        #  error resistant.
        test_mappings_result = generate_test_mappings(
            evg_api,
            project_config["project"],
            CommitLimit(stop_at_commit_sha=test_config["most_recent_project_commit_analyzed"]),
            test_config["source_file_regex"],
            test_config["test_file_regex"],
            module_name=test_config["module"],
            module_commit_limit=CommitLimit(
                stop_at_commit_sha=test_config["most_recent_module_commit_analyzed"]
            ),
            module_source_file_pattern=test_config["module_source_file_regex"],
            module_test_file_pattern=test_config["module_source_file_regex"],
        )

        project_config = ProjectConfig.get(mongo.project_config(), project_config["project"])
        project_config.test_config.update_most_recent_commits_analyzed(
            test_mappings_result.most_recent_project_commit_analyzed,
            test_mappings_result.most_recent_module_commit_analyzed,
        )
        project_config.save(mongo.project_config())

        if test_mappings_result.test_mappings_list:
            update_test_mappings(test_mappings_result.test_mappings_list, mongo)
        else:
            LOGGER.info("No test mappings generated")
    LOGGER.info("Finished test mapping updating")
