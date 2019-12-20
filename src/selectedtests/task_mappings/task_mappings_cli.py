"""Cli entry point for the task-mappings command."""
import json
import os.path

from datetime import datetime

import click
import structlog

from miscutils.logging_config import Verbosity

from selectedtests.config.logging_config import config_logging
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.helpers import get_evg_api
from selectedtests.task_mappings.create_task_mappings import generate_task_mappings
from selectedtests.task_mappings.update_task_mappings import update_task_mappings_since_last_commit
from selectedtests.task_mappings.version_limit import VersionLimit

LOGGER = structlog.get_logger(__name__)

EXTERNAL_LIBRARIES = ["evergreen.api", "urllib3"]
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.option(
    "--log-format",
    default="text",
    type=click.Choice(["text", "json"]),
    help="Format to write logs with.",
)
@click.pass_context
def cli(ctx, verbose: bool, log_format: str):
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
@click.option(
    "--build-variant-regex",
    type=str,
    help="Regex that will be used to decide what build variants are analyzed. Example: 'src.*'.",
)
@click.option(
    "--output-file",
    type=str,
    help="Path to a file where the task mappings should be written to. Example: 'output.txt'",
)
def create(
    ctx,
    evergreen_project: str,
    after: str,
    source_file_regex: str,
    module_name: str,
    module_source_file_regex: str,
    build_variant_regex: str,
    output_file: str,
):
    """Create the task mappings for a given evergreen project."""
    evg_api = ctx.obj["evg_api"]

    try:
        after_date = datetime.fromisoformat(after)
    except ValueError:
        raise click.ClickException(
            "The after date could not be parsed - make sure it's an iso date"
        )

    if module_name:
        if not module_source_file_regex:
            raise click.ClickException(
                "A module source file regex is required when a module is being analyzed"
            )

    LOGGER.info(f"Creating task mappings for {evergreen_project}")
    mappings, _ = generate_task_mappings(
        evg_api,
        evergreen_project,
        VersionLimit(stop_at_date=after_date),
        source_file_regex,
        module_name,
        module_source_file_regex,
        build_variant_regex,
    )
    json_dump = json.dumps(mappings, indent=4)

    if output_file:
        with open(output_file, "a") as f:
            f.write(json_dump)
    else:
        print(json_dump)

    LOGGER.info("Finished processing task mappings")


@cli.command()
@click.option(
    "--mongo-uri",
    type=str,
    default=lambda: os.environ.get("SELECTED_TESTS_MONGO_URI"),
    help="Mongo URI to connect to.",
)
@click.pass_context
def update(ctx, mongo_uri):
    """Process task mappings since they were last processed."""
    update_task_mappings_since_last_commit(ctx.obj["evg_api"], MongoWrapper.connect(mongo_uri))


def main():
    """Entry point into commandline."""
    return cli(obj={})
