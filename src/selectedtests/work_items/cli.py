"""Cli entry point to process work items."""
import click
import os
import structlog
import logging
import pytz

from datetime import datetime, timedelta
from evergreen.api import RetryingEvergreenApi
from evergreen.config import EvgAuth
from selectedtests.work_items.process_work_items import process_queued_work_items
from selectedtests.datasource.mongo_wrapper import MongoWrapper


def _get_evg_api():
    """
    Create an instance of the evergreen API based on environment variables.

    :return: Evergreen API instance.
    """
    evg_user = os.environ.get("EVG_API_USER")
    evg_api_key = os.environ.get("EVG_API_KEY")
    return RetryingEvergreenApi.get_api(auth=EvgAuth(evg_user, evg_api_key))


def _get_mongo_wrapper() -> MongoWrapper:
    """
    Get an instance of the mongo wrapper based on environment variables.

    :return: MongoWrapper instance.
    """
    mongo_uri = os.environ.get("SELECTED_TESTS_MONGO_URI")
    return MongoWrapper.connect(mongo_uri)


def _setup_logging(verbose: bool):
    """Set up logging configuration."""
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.pass_context
def cli(ctx, verbose: str):
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["mongo"] = _get_mongo_wrapper()
    ctx.obj["evg_api"] = _get_evg_api()

    _setup_logging(verbose)


@cli.command()
@click.pass_context
def process_test_mappings(ctx):
    """Process test mapping work items that have not yet been processed."""
    before_date = datetime.utcnow().replace(tzinfo=pytz.UTC)
    after_date = before_date - timedelta(days=6 * 30)  # 6 months
    process_queued_work_items(ctx.obj["evg_api"], ctx.obj["mongo"], after_date, before_date)


def main():
    """Entry point for setting up selected-tests db indexes."""
    return cli(obj={})
