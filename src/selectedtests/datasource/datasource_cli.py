"""Cli entry point to setup db indexes."""
import click
import structlog
import logging

from pymongo.collection import Collection
from pymongo import IndexModel, ASCENDING
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


def _setup_logging(verbose: bool):
    """Set up logging configuration."""
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.option("--mongo-uri", required=True, type=str, help="Mongo URI to connect to.")
@click.pass_context
def cli(ctx, verbose: bool, mongo_uri: str):
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["mongo"] = MongoWrapper.connect(mongo_uri)

    _setup_logging(verbose)


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
