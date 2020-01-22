"""Parsers used in selected tests API."""
from typing import List

from evergreen import Project
from fastapi import HTTPException

from selectedtests.evergreen_helper import get_evg_project


def changed_files_parser(changed_files: str) -> List[str]:
    return changed_files.split(",")


def retrieve_evergreen_project(project: str) -> Project:
    evergreen_project = get_evg_project(project)
    if not evergreen_project:
        raise HTTPException(status_code=404, detail="Evergreen project not found")
    return evergreen_project
