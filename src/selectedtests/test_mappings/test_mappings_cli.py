"""Cli entry point for the test-mappings command."""
import json
import os

from datetime import datetime

import click
import pytz
import structlog
from click import Context

from miscutils.logging_config import Verbosity

from selectedtests.config.logging_config import config_logging
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.helpers import get_evg_api
from selectedtests.test_mappings.commit_limit import CommitLimit
from selectedtests.test_mappings.create_test_mappings import generate_test_mappings
from selectedtests.test_mappings.update_test_mappings import update_test_mappings_since_last_commit

LOGGER = structlog.get_logger(__name__)

EXTERNAL_LIBRARIES = ["evergreen.api", "urllib3"]


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.option(
    "--log-format",
    default="text",
    type=click.Choice(["text", "json"]),
    help="Format to write logs with.",
)
@click.pass_context
def cli(ctx: Context, verbose: bool, log_format: str) -> None:
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["evg_api"] = get_evg_api()

    verbosity = Verbosity.DEBUG if verbose else Verbosity.INFO
    config_logging(verbosity, human_readable=log_format == "text")


@cli.command()
@click.pass_context
@click.argument("evergreen_project", required=True)
@click.option(
    "--after",
    type=str,
    help="The date to begin analyzing the project at - has to be an iso date. "
    "Example: 2019-10-11T19:10:38",
    required=True,
)
@click.option(
    "--source-file-regex",
    type=str,
    help="Regex that will be used to map what files mappings will be created for. "
    "Example: 'src.*'",
    required=True,
)
@click.option(
    "--test-file-regex", type=str, required=True, help="Regex to match test files in project."
)
@click.option(
    "--module-name",
    type=str,
    help="The name of the associated module that should be analyzed. Example: enterprise",
)
@click.option(
    "--module-source-file-regex",
    type=str,
    help="Regex that will be used to map what module files mappings will be created. "
    "Example: 'src.*'",
)
@click.option("--module-test-file-regex", type=str, help="Regex to match test files in module.")
@click.option(
    "--output-file",
    type=str,
    help="Path to a file where the task mappings should be written to. Example: 'output.txt'",
)
def create(
    ctx: Context,
    evergreen_project: str,
    after: str,
    source_file_regex: str,
    test_file_regex: str,
    module_name: str,
    module_source_file_regex: str,
    module_test_file_regex: str,
    output_file: str,
) -> None:
    """Create the test mappings for a given evergreen project."""
    evg_api = ctx.obj["evg_api"]

    try:
        after_date = datetime.fromisoformat(after).replace(tzinfo=pytz.UTC)
    except ValueError:
        raise click.ClickException(
            "The after date could not be parsed - make sure it's an iso date"
        )
        return

    if module_name:
        if not module_source_file_regex:
            raise click.ClickException(
                "A module source file regex is required when a module is being analyzed"
            )
            return
        if not module_test_file_regex:
            raise click.ClickException(
                "A module test file regex is required when a module is being analyzed"
            )
            return

    LOGGER.info(f"Creating test mappings for {evergreen_project}")

    test_mappings_result = generate_test_mappings(
        evg_api,
        evergreen_project,
        CommitLimit(stop_at_date=after_date),
        source_file_regex,
        test_file_regex,
        module_name=module_name,
        module_commit_limit=CommitLimit(stop_at_date=after_date),
        module_source_file_pattern=module_source_file_regex,
        module_test_file_pattern=module_test_file_regex,
    )

    json_dump = json.dumps(test_mappings_result.test_mappings_list, indent=4)

    if output_file:
        with open(output_file, "a") as f:
            f.write(json_dump)
    else:
        print(json_dump)

    LOGGER.info("Finished processing test mappings")


@cli.command()
@click.option(
    "--mongo-uri",
    type=str,
    default=lambda: os.environ.get("SELECTED_TESTS_MONGO_URI"),
    help="Mongo URI to connect to.",
)
@click.pass_context
def update(ctx: Context, mongo_uri: str) -> None:
    """Process test mappings since they were last processed."""
    update_test_mappings_since_last_commit(ctx.obj["evg_api"], MongoWrapper.connect(mongo_uri))


def main() -> None:
    """Entry point into commandline."""
    return cli(obj={})
