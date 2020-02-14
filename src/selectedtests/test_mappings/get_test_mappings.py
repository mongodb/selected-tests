"""Script to get test mappings."""
from decimal import Decimal
from typing import List

from pymongo.collection import Collection


def get_correlated_test_mappings(
    collection: Collection, changed_source_files: List[str], project: str, threshold: Decimal
) -> List[dict]:
    """
    Retrieve test mappings associated with a given evergreen project and list of source files.

    :param collection: Collection to act on.
    :param changed_source_files: List of source files for which test mappings should be retrieved.
    :param project: The name of the evergreen project to analyze.
    :param threshold: Min threshold desired for test_file_seen_count/source_file_seen_count ratio.
    :return: A list of test mappings for the changed files.
    """
    return list(
        collection.aggregate(
            [
                {"$match": {"project": project, "source_file": {"$in": changed_source_files}}},
                # lookup could also use a pipeline but in certain cases this won't use an
                # index, so a lookup followed by a filter can be quicker.
                {
                    "$lookup": {
                        "from": f"{collection.name}_test_files",
                        "localField": "source_file",
                        "foreignField": "source_file",
                        "as": "test_files",
                    }
                },
                # filter out the array elements below threshold.
                {
                    "$addFields": {
                        "test_files": {
                            "$filter": {
                                "input": "$test_files",
                                "as": "test_file",
                                "cond": {
                                    "$gte": [
                                        {
                                            "$divide": [
                                                "$$test_file.test_file_seen_count",
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
                {
                    "$project": {
                        "_id": False,
                        "test_files._id": False,
                        "test_files.source_file": False,
                    }
                },
            ]
        )
    )
