"""Logging utilities."""
from enum import IntEnum

from miscutils.logging_config import LogFormat, default_logging

EXTERNAL_LOGGERS = [
    "evergreen",
    "oauthlib",
    "requests",
    "requests_oauthlib",
    "urllib3.connectionpool",
]


class Verbosity(IntEnum):
    """Verbosity level for logging. The higher the level the more logging we do."""

    WARNING = 0
    INFO = 1
    DEBUG = 2


def config_logging(verbosity: int, human_readable: bool = True) -> None:
    """
    Configure logging based on the given verbosity.

    :param verbosity: Amount of verbosity to use.
    :param human_readable: Should output be human readable.
    """
    log_format = LogFormat.TEXT if human_readable else LogFormat.JSON
    default_logging(verbosity, log_format, EXTERNAL_LOGGERS)
