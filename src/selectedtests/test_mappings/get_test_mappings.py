"""Script to get test mappings."""
from decimal import Decimal
from typing import List

from pymongo.collection import Collection


def _exclude_test_files_below_threshold(test_mapping: dict, threshold: Decimal) -> dict:
    """
    Retrieve test mappings associated with a given evergreen project and list of source files.

    :param test_mapping: The test mapping being analyzed.
    :param threshold: Min threshold desired for test_file_seen_count/source_file_seen_count ratio.
    :return: The test mapping minus the test_files that fell below the desired threshold.
    """
    for test_file in list(test_mapping["test_files"]):
        if (test_file["test_file_seen_count"] / test_mapping["source_file_seen_count"]) < threshold:
            test_mapping["test_files"].remove(test_file)

    return test_mapping


def get_correlated_test_mappings(
    collection: Collection, changed_source_files: List[str], project: str, threshold: Decimal
) -> List[dict]:
    """
    Retrieve test mappings associated with a given evergreen project and list of source files.

    :param collection: Collection to act on.
    :param changed_source_files: List of source files for which test mappings should be retrieved.
    :param evergreen_project: The name of the evergreen project to analyze.
    :param threshold: Min threshold desired for test_file_seen_count/source_file_seen_count ratio.
    :return: A list of test mappings for the changed files.
    """
    test_mappings = []
    for changed_file in changed_source_files:
        test_mappings_data = collection.find(
            {"project": project, "source_file": changed_file}, {"_id": False}
        )
        test_mappings.extend(
            [
                _exclude_test_files_below_threshold(test_mapping, threshold)
                for test_mapping in test_mappings_data
            ]
        )
    return test_mappings
