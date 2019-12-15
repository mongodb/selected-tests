"""Cli entry point to process work items."""
import click
import pytz

from datetime import datetime, timedelta
from selectedtests.work_items.process_test_mapping_work_items import (
    process_queued_test_mapping_work_items,
    update_test_mappings_since_last_commit,
)
from selectedtests.work_items.process_task_mapping_work_items import (
    process_queued_task_mapping_work_items,
    update_task_mappings_since_last_commit,
)
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.helpers import get_evg_api, setup_logging
from selectedtests.evergreen_helper import get_evg_project
from selectedtests.work_items.task_mapping_work_item import ProjectTaskMappingWorkItem
from selectedtests.work_items.test_mapping_work_item import ProjectTestMappingWorkItem

DEFAULT_WEEKS_BACK = 24


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.option("--mongo-uri", required=True, type=str, help="Mongo URI to connect to.")
@click.pass_context
def cli(ctx, verbose: str, mongo_uri: str):
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["mongo"] = MongoWrapper.connect(mongo_uri)
    ctx.obj["evg_api"] = get_evg_api()

    setup_logging(verbose)


@cli.command()
@click.option("--project", type=str, required=True, help="Evergreen project to add.")
@click.option(
    "--src-regex", type=str, required=True, help="Regular expression for project source files."
)
@click.option(
    "--test-file-regex", type=str, required=True, help="Regular expression for project test files."
)
@click.pass_context
def create_test_mapping(ctx, project: str, src_regex: str, test_file_regex: str):
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
    work_item.insert(ctx.obj["mongo"].test_mappings_queue())


@cli.command()
@click.option(
    "--weeks-back", type=int, default=DEFAULT_WEEKS_BACK, help="Number of weeks back to process."
)
@click.pass_context
def process_test_mappings(ctx, weeks_back):
    """Process test mapping work items that have not yet been processed."""
    # For test mappings, after_date is compared against git commit committed_datetime, which is
    # stored in a UTC date format that is UTC offset-aware. So after_date needs to be offset-aware,
    # which is why we add tzinfo below.
    now = datetime.utcnow().replace(tzinfo=pytz.UTC)
    after_date = now - timedelta(weeks=weeks_back)
    process_queued_test_mapping_work_items(ctx.obj["evg_api"], ctx.obj["mongo"], after_date)


@cli.command()
@click.pass_context
def update_test_mappings(ctx):
    """Process test mappings since they were last processed."""
    update_test_mappings_since_last_commit(ctx.obj["evg_api"], ctx.obj["mongo"])


@cli.command()
@click.option("--project", type=str, required=True, help="Evergreen project to add.")
@click.option(
    "--src-regex", type=str, required=True, help="Regular expression for project source files."
)
@click.option("--build-regex", type=str, help="Regular expression for build variants.")
@click.pass_context
def create_task_mapping(ctx, project: str, src_regex: str, build_regex: str):
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
    work_item.insert(ctx.obj["mongo"].task_mappings_queue())


@cli.command()
@click.option(
    "--weeks-back", type=int, default=DEFAULT_WEEKS_BACK, help="Number of weeks back to process."
)
@click.pass_context
def process_task_mappings(ctx, weeks_back):
    """Process task mapping work items that have not yet been processed."""
    # For task mappings, after_date is compared against evergreen version create_time, which is
    # stored in a UTC date format that is not UTC offset-aware. So after_date does not need to be
    # offset-aware.
    after_date = datetime.utcnow() - timedelta(weeks=weeks_back)
    process_queued_task_mapping_work_items(ctx.obj["evg_api"], ctx.obj["mongo"], after_date)


@cli.command()
@click.pass_context
def update_task_mappings(ctx):
    """Process task mappings since they were last processed."""
    update_task_mappings_since_last_commit(ctx.obj["evg_api"], ctx.obj["mongo"])


def main():
    """Entry point for setting up selected-tests db indexes."""
    return cli(obj={}, auto_envvar_prefix="SELECTED_TESTS")
