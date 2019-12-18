"""Methods to update task mappings for a project."""
import structlog

from evergreen.api import EvergreenApi

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.project_config import ProjectConfig
from selectedtests.task_mappings.create_task_mappings import generate_task_mappings
from selectedtests.task_mappings.version_limit import VersionLimit

LOGGER = structlog.get_logger()


def update_task_mappings_since_last_commit(evg_api: EvergreenApi, mongo: MongoWrapper):
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
            mongo.task_mappings().insert_many(mappings)
        else:
            LOGGER.info("No task mappings generated")
    LOGGER.info("Finished task mapping updating")
