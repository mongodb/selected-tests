import structlog

from evergreen.api import EvergreenApi

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.task_mappings.create_task_mappings import generate_task_mappings
from selectedtests.task_mappings.version_limit import VersionLimit

LOGGER = structlog.get_logger()


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
