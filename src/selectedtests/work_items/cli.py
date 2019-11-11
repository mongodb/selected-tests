"""Cli entry point to process work items."""
import click
import pytz

from datetime import datetime, timedelta
from selectedtests.work_items.process_work_items import process_queued_work_items
from selectedtests.helpers import get_evg_api, get_mongo_wrapper, setup_logging


@click.group()
@click.option("--verbose", is_flag=True, default=False, help="Enable verbose logging.")
@click.pass_context
def cli(ctx, verbose: str):
    """Entry point for the cli interface. It sets up the evg api instance and logging."""
    ctx.ensure_object(dict)
    ctx.obj["mongo"] = get_mongo_wrapper()
    ctx.obj["evg_api"] = get_evg_api()

    setup_logging(verbose)


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
