"""Methods to update test mappings for a project."""
import structlog

from evergreen.api import EvergreenApi

from selectedtests.test_mappings.create_test_mappings import generate_test_mappings
from selectedtests.test_mappings.commit_limit import CommitLimit
from selectedtests.datasource.mongo_wrapper import MongoWrapper

LOGGER = structlog.get_logger()


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
            module_source_file_pattern=project_config["module_source_re"],
            module_test_file_pattern=project_config["module_source_re"],
        )
        _update_test_mappings_config(mongo, project_config["project"], test_mappings_result)
        if test_mappings_result.test_mappings_list:
            mongo.test_mappings().insert_many(test_mappings_result.test_mappings_list)
        else:
            LOGGER.info("No test mappings generated")
    LOGGER.info("Finished test mapping updating")
