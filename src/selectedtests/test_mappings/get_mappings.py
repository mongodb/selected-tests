"""Script to get test mappings."""
from typing import List
from bson import json_util

from pymongo.collection import Collection


def get_correlated_test_mappings(
    collection: Collection, changed_source_files: List[str], project: str
) -> List[dict]:
    """
    Retrieve test mappings associated with a given evergreen project and list of source files.

    :param collection: Collection to act on.
    :param changed_source_files: List of source files for which test mappings should be retrieved.
    :param evergreen_project: The name of the evergreen project to analyze.
    :return: A list of test mappings for the evergreen project and list of changed files.
    """
    test_mappings = []
    for changed_file in changed_source_files:
        test_mappings_data = collection.find(
            {"project": project, "source_file": changed_file}, {"_id": False}
        )
        test_mappings.extend(test_mappings_data)
    return json_util.dumps(test_mappings)
