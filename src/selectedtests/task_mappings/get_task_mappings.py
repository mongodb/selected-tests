"""Script to get task mappings."""
from decimal import Decimal
from typing import List

import inject
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.injection_helper import remap_for_injection


@inject.autoparams()
@remap_for_injection
def get_correlated_task_mappings(
        db: MongoWrapper, changed_source_files: List[str], project: str, threshold: Decimal
) -> List[dict]:
    """
    Retrieve task mappings associated with a given evergreen project and list of source files.

    :param project: The name of the evergreen project to analyze.
    :param db: db containing task mappings collection.
    :param changed_source_files: List of source files for which task mappings should be retrieved.
    :param threshold: Min threshold desired for flip_count/source_file_seen_count ratio.
    :return: A list of task mappings for the changed files.
    """
    collection = db.task_mappings()
    return list(
        collection.aggregate(
            [
                {"$match": {"project": project, "source_file": {"$in": changed_source_files}}},
                {
                    "$lookup": {
                        "from": f"{collection.name}_tasks",
                        "localField": "_id",
                        "foreignField": "task_mapping_id",
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
                {"$project": {"_id": False, "tasks._id": False, "tasks.task_mapping_id": False}},
            ]
        )
    )
