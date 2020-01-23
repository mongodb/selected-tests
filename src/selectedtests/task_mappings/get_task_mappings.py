"""Script to get task mappings."""
from decimal import Decimal
from typing import List

from pymongo.collection import Collection


def _exclude_tasks_below_threshold(task_mapping: dict, threshold: Decimal) -> dict:
    """
    Retrieve task mappings associated with a given evergreen project and list of source files.

    :param task_mapping: The task mapping being analyzed.
    :param threshold: Min threshold desired for flip_count/source_file_seen_count ratio.
    :return: The task mapping minus the tasks that fell below the desired threshold.
    """
    for task in list(task_mapping["tasks"]):
        if (task["flip_count"] / task_mapping["source_file_seen_count"]) < threshold:
            task_mapping["tasks"].remove(task)

    return task_mapping


def get_correlated_task_mappings(
        collection: Collection, changed_source_files: List[str], project: str, threshold: Decimal,
) -> List[dict]:
    """
    Retrieve task mappings associated with a given evergreen project and list of source files.

    :param project: The name of the evergreen project to analyze.
    :param collection: Collection to act on.
    :param changed_source_files: List of source files for which task mappings should be retrieved.
    :param threshold: Min threshold desired for flip_count/source_file_seen_count ratio.
    :return: A list of task mappings for the changed files.
    """
    task_mappings = []
    for changed_file in changed_source_files:
        task_mappings_data = collection.find(
            {"project": project, "source_file": changed_file}, {"_id": False}
        )
        task_mappings.extend(
            [
                _exclude_tasks_below_threshold(task_mapping, threshold)
                for task_mapping in task_mappings_data
            ]
        )
    return task_mappings
