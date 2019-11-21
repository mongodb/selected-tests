"""Cli entry point for the test-mappings command."""
import click
import json
import logging
import pytz
import re
import structlog

from datetime import datetime
from evergreen.api import RetryingEvergreenApi
from selectedtests.test_mappings.create_mappings import generate_test_mappings

LOGGER = structlog.get_logger(__name__)

EXTERNAL_LIBRARIES = ["evergreen.api", "urllib3"]


def _setup_logging(verbose: bool):
    """Set up logging configuration."""
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)
    for external_lib in EXTERNAL_LIBRARIES:
        logging.getLogger(external_lib).setLevel(logging.WARNING)


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.pass_context
def cli(ctx, verbose: str):
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["evg_api"] = RetryingEvergreenApi.get_api(use_config_file=True)

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
    "--before",
    type=str,
    help="The date to stop analyzing the project at - has to be an iso date. "
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
    ctx,
    evergreen_project: str,
    after: str,
    before: str,
    source_file_regex: str,
    test_file_regex: str,
    module_name: str,
    module_source_file_regex: str,
    module_test_file_regex: str,
    output_file: str,
):
    """Create the test mappings for a given evergreen project."""
    evg_api = ctx.obj["evg_api"]

    try:
        after_date = datetime.fromisoformat(after).replace(tzinfo=pytz.UTC)
        before_date = datetime.fromisoformat(before).replace(tzinfo=pytz.UTC)
    except ValueError:
        raise click.ClickException(
            "The after or before date could not be parsed - make sure it's an iso date"
        )
        return

    source_re = re.compile(source_file_regex)
    test_re = re.compile(test_file_regex)
    module_source_re = None
    module_test_re = None
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
        module_source_re = re.compile(module_source_file_regex)
        module_test_re = re.compile(module_test_file_regex)

    LOGGER.info(f"Creating test mappings for {evergreen_project}")

    test_mappings_list = generate_test_mappings(
        evg_api,
        evergreen_project,
        source_re,
        test_re,
        after_date,
        before_date,
        module_name,
        module_source_re,
        module_test_re,
    )

    json_dump = json.dumps(test_mappings_list, indent=4)

    if output_file:
        with open(output_file, "a") as f:
            f.write(json_dump)
    else:
        print(json_dump)

    LOGGER.info("Finished processing test mappings")


def main():
    """Entry point into commandline."""
    return cli(obj={})
