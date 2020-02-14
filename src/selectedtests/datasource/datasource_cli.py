"""Cli entry point to setup db indexes."""
import click
import structlog

from click import Context
from miscutils.logging_config import Verbosity
from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection

from selectedtests.config.logging_config import config_logging
from selectedtests.datasource.mongo_wrapper import MongoWrapper

LOGGER = structlog.get_logger()


def setup_queue_indexes(collection: Collection) -> None:
    """
    Create appropriate indexes for ProjectTestMappingWorkItems.

    :param collection: Collection to add indexes to.
    """
    index = IndexModel([("project", ASCENDING)], unique=True)
    collection.create_indexes([index])
    LOGGER.info("Adding indexes for collection", collection=collection.name)


def setup_mappings_indexes(collection: Collection) -> None:
    """
    Create appropriate indexes for the test and task mappings collections.

    :param collection: Collection to add indexes to.
    """
    # project, source_file on it's own could be unique, but the repo and branch are needed when
    # there is a module.
    index = IndexModel(
        [
            ("project", ASCENDING),
            ("repo", ASCENDING),
            ("branch", ASCENDING),
            ("source_file", ASCENDING),
        ],
        unique=True,
    )
    collection.create_indexes([index])
    LOGGER.info("Adding indexes for collection", collection=collection.name)


def setup_mappings_tasks_indexes(collection: Collection) -> None:
    """
    Create appropriate indexes for the mapping tasks collection.

    The indexes must support both the $lookup operation and uniqueness constraints.

    :param collection: Collection to add indexes to.
    """
    # task_mapping_id simplifies the index (but then requires a find_and_update_one for the
    # insert / upsert.
    index = IndexModel(
        [("task_mapping_id", ASCENDING), ("name", ASCENDING), ("variant", ASCENDING)], unique=True
    )
    collection.create_indexes([index])
    LOGGER.info("Adding indexes for collection", collection=collection.name)


def setup_mappings_test_files_indexes(collection: Collection) -> None:
    """
    Create appropriate indexes for the mapping test files collection.

    The indexes must support both the $lookup operation and uniqueness constraints.

    :param collection: Collection to add indexes to.
    """
    # test_mapping_id simplifies the index (but then requires a find_and_update_one for the
    # insert / upsert.
    index = IndexModel([("test_mapping_id", ASCENDING), ("name", ASCENDING)], unique=True)
    collection.create_indexes([index])
    LOGGER.info("Adding indexes for collection", collection=collection.name)


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.option("--mongo-uri", required=True, type=str, help="Mongo URI to connect to.")
@click.pass_context
def cli(ctx: Context, verbose: bool, mongo_uri: str) -> None:
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["mongo"] = MongoWrapper.connect(mongo_uri)

    verbosity = Verbosity.DEBUG if verbose else Verbosity.INFO
    config_logging(verbosity, human_readable=False)


@cli.command()
@click.pass_context
def create_indexes(ctx: Context) -> None:
    """Initialize the mongo database with proper indexes."""
    # Creating index no-ops if index already exists
    setup_queue_indexes(ctx.obj["mongo"].test_mappings_queue())
    setup_queue_indexes(ctx.obj["mongo"].task_mappings_queue())

    setup_mappings_indexes(ctx.obj["mongo"].test_mappings())
    setup_mappings_indexes(ctx.obj["mongo"].task_mappings())

    setup_mappings_test_files_indexes(ctx.obj["mongo"].test_mappings_test_files())
    setup_mappings_tasks_indexes(ctx.obj["mongo"].task_mappings_tasks())


def main() -> None:
    """Entry point for setting up selected-tests db indexes."""
    return cli(obj={}, auto_envvar_prefix="SELECTED_TESTS")
