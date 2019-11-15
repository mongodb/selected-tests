"""Script to get test mappings."""
from typing import List
from pymongo.collection import Collection


def _parse_test_mapping(test_mapping: dict) -> dict:
    exclude_keys = ["_id"]
    return {k: test_mapping[k] for k in set(list(test_mapping.keys())) - set(exclude_keys)}


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
        test_mappings_data = collection.find({"project": project, "source_file": changed_file})
        test_mappings.extend(
            [_parse_test_mapping(test_mapping) for test_mapping in test_mappings_data]
        )
    return test_mappings
