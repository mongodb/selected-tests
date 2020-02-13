"""Methods to update test mappings for a project."""
from typing import Dict, List

import structlog

from evergreen.api import EvergreenApi
from pymongo import UpdateOne

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.project_config import ProjectConfig
from selectedtests.test_mappings.commit_limit import CommitLimit
from selectedtests.test_mappings.create_test_mappings import generate_test_mappings

LOGGER = structlog.get_logger()


def update_test_mappings(test_mappings: List[Dict], mongo: MongoWrapper) -> None:
    """
    Update test mappings in the test mappings project config collection.

    :param test_mappings: A list of test mappings.
    :param mongo: An instance of MongoWrapper.
    """
    for mapping in test_mappings:
        # get the test_files to update and remove from the mapping document.
        test_files = mapping.get("test_files", [])
        del mapping["test_files"]

        # get the value to inc  and remove from the mapping document (otherwise we would double
        # increment).
        source_file_seen_count = mapping["source_file_seen_count"]
        del mapping["source_file_seen_count"]

        # we don't need this in the $set as it is supplied by query.
        source_file = mapping["source_file"]
        del mapping["source_file"]

        result = mongo.test_mappings().update_one(
            {"source_file": source_file},
            {"$set": mapping, "$inc": {"source_file_seen_count": source_file_seen_count}},
            upsert=True,
        )
        LOGGER.debug(
            "update_one test_mappings",
            result=result,
            source_file=source_file,
            inc=source_file_seen_count,
        )
        if test_files:
            files_operations = []
            for test_file in test_files:
                update_test_file = UpdateOne(
                    {"source_file": source_file, "name": test_file["name"]},
                    {"$inc": {"test_file_seen_count": test_file["test_file_seen_count"]}},
                    upsert=True,
                )
                files_operations.append(update_test_file)

            result = mongo.test_mappings_test_files().bulk_write(files_operations, ordered=True)
            LOGGER.debug("bulk_write", result=result.bulk_api_result, source_file=source_file)


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

        # TODO: if generate_test_mappings yielded the mappings in ascending order and updates were
        #  written in transactions, then this code would be quicker, restartable and error
        #  resistant.
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
