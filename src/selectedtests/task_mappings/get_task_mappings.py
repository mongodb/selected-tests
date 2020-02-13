"""Script to get task mappings."""
from decimal import Decimal
from typing import List

from pymongo.collection import Collection


def get_correlated_task_mappings(
    collection: Collection, changed_source_files: List[str], project: str, threshold: Decimal
) -> List[dict]:
    """
    Retrieve task mappings associated with a given evergreen project and list of source files.

    :param project: The name of the evergreen project to analyze.
    :param collection: Collection to act on.
    :param changed_source_files: List of source files for which task mappings should be retrieved.
    :param threshold: Min threshold desired for flip_count/source_file_seen_count ratio.
    :return: A list of task mappings for the changed files.
    """
    task_mappings = list(
        collection.aggregate(
            [
                {"$match": {"project": project, "source_file": {"$in": changed_source_files}}},
                # lookup could also use a pipeline but in certain cases this won't use an
                # index, so a lookup followed by a filter can be quicker.
                {
                    "$lookup": {
                        "from": f"{collection.name}_tasks",
                        "localField": "source_file",
                        "foreignField": "source_file",
                        "as": "tasks",
                    }
                },
                # filter out the array elements below threshold.
                {
                    "$addFields": {
                        "tasks": {
                            "$filter": {
                                "input": "$tasks",
                                "as": "task",
                                "cond": {
                                    "$gte": [
                                        {
                                            "$divide": [
                                                "$$task.flip_count",
                                                "$source_file_seen_count",
                                            ]
                                        },
                                        float(threshold),
                                    ]
                                },
                            }
                        }
                    }
                },
                # clean up the output before returning.
                {"$project": {"_id": False, "tasks._id": False, "tasks.source_file": False}},
            ]
        )
    )
    return task_mappings
