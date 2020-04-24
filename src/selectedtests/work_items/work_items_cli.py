"""Cli entry point to process work items."""
from datetime import datetime

import click
import inject
import pytz

from click import Context
from dateutil.relativedelta import relativedelta
from evergreen import EvergreenApi
from miscutils.logging_config import Verbosity

from selectedtests.config.logging_config import config_logging
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.evergreen_helper import get_evg_project
from selectedtests.helpers import get_evg_api
from selectedtests.work_items.process_task_mapping_work_items import (
    process_queued_task_mapping_work_items,
)
from selectedtests.work_items.process_test_mapping_work_items import (
    process_queued_test_mapping_work_items,
)
from selectedtests.work_items.task_mapping_work_item import ProjectTaskMappingWorkItem
from selectedtests.work_items.test_mapping_work_item import ProjectTestMappingWorkItem

DEFAULT_YEARS_BACK = 3


def _get_after_date(years_back: int) -> datetime:
    """
    Create an after_date for evergreen versions and git commits to be compared against.

    :param years_back: Number of years back set date to.
    :return: After date in UTC offset-aware format.
    """
    #  After_date is compared against evergreen version create_time and git commit
    #  committed_datetime, which are stored in a UTC date format that is UTC offset-aware. So
    #  after_date needs to be offset-aware, which is why we add tzinfo below.
    now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    return now - relativedelta(years=years_back)


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.option(
    "--log-format",
    default="text",
    type=click.Choice(["text", "json"]),
    help="Format to write logs with.",
)
@click.option("--mongo-uri", required=True, type=str, help="Mongo URI to connect to.")
@click.pass_context
def cli(ctx: Context, verbose: str, log_format: str, mongo_uri: str) -> None:
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["mongo"] = MongoWrapper.connect(mongo_uri)
    ctx.obj["evg_api"] = get_evg_api()

    def dependencies(binder: inject.Binder):
        binder.bind(EvergreenApi, ctx.obj["evg_api"])
        binder.bind('EvergreenApi', ctx.obj["evg_api"])
        binder.bind(MongoWrapper, ctx.obj["mongo"])
        binder.bind('MongoWrapper', ctx.obj["mongo"])
    inject.configure(dependencies)

    verbosity = Verbosity.DEBUG if verbose else Verbosity.INFO
    config_logging(verbosity, human_readable=log_format == "text")


@cli.command()
@click.option("--project", type=str, required=True, help="Evergreen project to add.")
@click.option(
    "--src-regex", type=str, required=True, help="Regular expression for project source files."
)
@click.option(
    "--test-file-regex", type=str, required=True, help="Regular expression for project test files."
)
@click.pass_context
def create_test_mapping(ctx: Context, project: str, src_regex: str, test_file_regex: str) -> None:
    """
    Add a project to the queue to be tracked for test mappings.

    This command is meant for testing purposes only. Adding new projects to the task mappings
    should normally be done via the REST API.
    \f
    :param ctx: Command Context.
    :param project: Evergreen project to add to queue.
    :param src_regex: Regular expression for project source files.
    :param test_file_regex: Regular expression for project test files.
    """
    evergreen_project = get_evg_project(ctx.obj["evg_api"], project)
    if not evergreen_project:
        raise ValueError("Evergreen project not found")

    work_item = ProjectTestMappingWorkItem.new_test_mappings(project, src_regex, test_file_regex)
    work_item.insert()


@cli.command()
@click.option(
    "--years-back", type=int, default=DEFAULT_YEARS_BACK, help="Number of years back to process."
)
@click.pass_context
def process_test_mappings(ctx: Context, years_back: int) -> None:
    """
    Process test mapping work items that have not yet been processed.

    :param years_back: Number of years back to process.
    """
    after_date = _get_after_date(years_back)
    process_queued_test_mapping_work_items(ctx.obj["evg_api"], ctx.obj["mongo"], after_date)


@cli.command()
@click.option("--project", type=str, required=True, help="Evergreen project to add.")
@click.option(
    "--src-regex", type=str, required=True, help="Regular expression for project source files."
)
@click.option("--build-regex", type=str, help="Regular expression for build variants.")
@click.pass_context
def create_task_mapping(ctx: Context, project: str, src_regex: str, build_regex: str) -> None:
    """
    Add a project to the queue to be tracked for task mappings.

    This command is meant for testing purposes only. Adding new projects to the task mappings
    should normally be done via the REST API.
    \f
    :param ctx: Command Context.
    :param project: Evergreen project to add to queue.
    :param src_regex: Regular expression for project source files.
    :param build_regex: Regular expression for build variants.
    """
    evergreen_project = get_evg_project(ctx.obj["evg_api"], project)
    if not evergreen_project:
        raise ValueError("Evergreen project not found")

    work_item = ProjectTaskMappingWorkItem.new_task_mappings(
        project, src_regex, build_variant_regex=build_regex
    )
    work_item.insert()


@cli.command()
@click.option(
    "--years-back", type=int, default=DEFAULT_YEARS_BACK, help="Number of years back to process."
)
@click.pass_context
def process_task_mappings(ctx: Context, years_back: int) -> None:
    """
    Process task mapping work items that have not yet been processed.

    :param years_back: Number of years back to process.
    """
    after_date = _get_after_date(years_back)
    process_queued_task_mapping_work_items(ctx.obj["evg_api"], ctx.obj["mongo"], after_date)


def main() -> None:
    """Entry point for setting up selected-tests db indexes."""
    return cli(obj={}, auto_envvar_prefix="SELECTED_TESTS")
