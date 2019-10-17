"""Cli entry point for the mappings command."""
import os.path
import json
import logging
from datetime import datetime
import re

from evergreen.api import CachedEvergreenApi
import click
import structlog

from selectedtests.task_mappings.task_mappings import TaskMappings

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
    ctx.obj["evg_api"] = CachedEvergreenApi.get_api(use_config_file=True)

    _setup_logging(verbose)


@cli.command()
@click.pass_context
@click.argument("evergreen_project", required=True)
@click.option(
    "--start",
    type=str,
    help="The date to begin analyzing the project at - has to be an iso date. "
    "Example: 2019-10-11T19:10:38",
    required=True,
)
@click.option(
    "--end",
    type=str,
    help="The date to stop analyzing the project at - has to be an iso date. "
    "Example: 2019-10-11T19:10:38",
    required=True,
)
@click.option(
    "--org-name",
    type=str,
    help="The Github organization name - defaults to mongodb",
    default="mongodb",
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
    "--output-file",
    type=str,
    help="Path to a file where the task mappings should be written to. Example: 'output.txt'",
)
def task(
    ctx,
    evergreen_project: str,
    start: str,
    end: str,
    org_name: str,
    source_file_regex: str,
    module_name: str,
    module_source_file_regex: str,
    output_file: str,
):
    """Create the task mappings for a given evergreen project."""
    evg_api = ctx.obj["evg_api"]

    try:
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
    except ValueError as e:
        LOGGER.error(str(e))
        LOGGER.error("The start or end date could not be parsed - make sure it's an iso date")
        return

    file_regex = re.compile(source_file_regex)

    module_file_regex = None
    if module_name is not None and module_name != "":
        if module_source_file_regex is None:
            LOGGER.error("A module source file regex is required when a module is being analyzed")
            return
        else:
            module_file_regex = re.compile(module_source_file_regex)

    LOGGER.info(f"Creating task mappings for {evergreen_project}")

    mappings = TaskMappings.create_task_mappings(
        evg_api,
        evergreen_project,
        start_date,
        end_date,
        org_name,
        file_regex,
        module_name,
        module_file_regex,
    )

    transformed_mappings = mappings.transform()

    json_dump = json.dumps(transformed_mappings, indent=4)

    if output_file is not None and output_file != "":
        f = open(output_file, "a")
        f.write(json_dump)
        f.close()
    else:
        print(json_dump)

    LOGGER.info("Finished processing task mappings")


def main():
    """Entry point into commandline."""
    return cli(obj={})
