"""Parsers used in selected tests API."""
from typing import List

from evergreen import Project, EvergreenApi
from fastapi import HTTPException, Depends
from starlette.requests import Request

from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.evergreen_helper import get_evg_project


def changed_files_parser(changed_files: str) -> List[str]:
    return changed_files.split(",")


def get_db(request: Request) -> MongoWrapper:
    return request.app.state.db


def get_evg(request: Request) -> MongoWrapper:
    return request.app.state.evg_api


def retrieve_evergreen_project(project: str, api: EvergreenApi = Depends(get_evg)) -> Project:
    evergreen_project = get_evg_project(api, project)
    if not evergreen_project:
        raise HTTPException(status_code=404, detail="Evergreen project not found")
    return evergreen_project
