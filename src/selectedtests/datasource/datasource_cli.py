"""Cli entry point to setup db indexes."""
import click
import structlog

from miscutils.logging_config import Verbosity
from pymongo import ASCENDING, IndexModel
from pymongo.collection import Collection
from selectedtests.config.logging_config import config_logging
from selectedtests.datasource.mongo_wrapper import MongoWrapper

LOGGER = structlog.get_logger()


def setup_indexes(collection: Collection):
    """
    Create appropriate indexes for ProjectTestMappingWorkItems.

    :param collection: Collection to add indexes to.
    """
    index = IndexModel([("project", ASCENDING)], unique=True)
    collection.create_indexes([index])
    LOGGER.info("Adding indexes for collection", collection=collection.name)


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.option("--mongo-uri", required=True, type=str, help="Mongo URI to connect to.")
@click.pass_context
def cli(ctx, verbose: bool, mongo_uri: str):
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["mongo"] = MongoWrapper.connect(mongo_uri)

    verbosity = Verbosity.DEBUG if verbose else Verbosity.INFO
    config_logging(verbosity, human_readable=False)


@cli.command()
@click.pass_context
def create_indexes(ctx):
    """Initialize the mongo database with proper indexes."""
    # Creating index no-ops if index already exists
    setup_indexes(ctx.obj["mongo"].test_mappings_queue())
    setup_indexes(ctx.obj["mongo"].task_mappings_queue())


def main():
    """Entry point for setting up selected-tests db indexes."""
    return cli(obj={}, auto_envvar_prefix="SELECTED_TESTS")
