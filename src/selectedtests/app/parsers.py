"""Helper functions for selected tests API."""
from typing import List


def parse_changed_files(changed_files: str) -> List[str]:
    """
    Get the list of strings specified in CSV format under change_files query parameter.

    :param changed_files: The CSV string.
    :return: The parsed list of strings.
    """
    return changed_files.split(",")
