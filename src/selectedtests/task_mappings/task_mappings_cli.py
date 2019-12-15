"""Cli entry point for the task-mappings command."""
import os.path
import json
import logging

from datetime import datetime

import click
import structlog

from selectedtests.helpers import get_evg_api
from selectedtests.task_mappings.create_task_mappings import generate_task_mappings
from selectedtests.task_mappings.version_limit import VersionLimit

LOGGER = structlog.get_logger(__name__)

EXTERNAL_LIBRARIES = ["evergreen.api", "urllib3"]
CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def _setup_logging(verbose: bool):
    """Set up the logging configuration."""
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)
    for external_lib in EXTERNAL_LIBRARIES:
        logging.getLogger(external_lib).setLevel(logging.WARNING)


@click.group()
@click.pass_context
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
def cli(ctx, verbose: bool):
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["evg_api"] = get_evg_api()

    _setup_logging(verbose)


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
    help="Regex that will be used to decide what build variants are analyzed. "
    "Example: 'src.*'. Defaults to '!.*'",
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


def main():
    """Entry point into commandline."""
    return cli(obj={})
