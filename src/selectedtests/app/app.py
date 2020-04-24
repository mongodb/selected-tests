"""Application to serve API of selected-tests service."""
import inject

from evergreen import EvergreenApi
from fastapi import FastAPI

from selectedtests.app.controllers import (
    health_controller,
    project_task_mappings_controller,
    project_test_mappings_controller,
)
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.helpers import get_evg_api, get_mongo_wrapper


def create_app() -> FastAPI:
    """
    Create a selected-tests REST API.

    :return: The application.
    """
    app = FastAPI(
        version="1.0",
        title="Selected Tests Service",
        description="This service is used to predict which tests and tasks need to run based on"
        " code changes.",
        docs_url="/swagger",
        openapi_url="/swagger.json",
    )
    app.include_router(health_controller.router, prefix="/health", tags=["health"])
    app.include_router(
        project_task_mappings_controller.router,
        prefix="/projects/{project}/task-mappings",
        tags=["projects"],
    )
    app.include_router(
        project_test_mappings_controller.router,
        prefix="/projects/{project}/test-mappings",
        tags=["projects"],
    )

    def dependencies(binder: inject.Binder):
        binder.bind(EvergreenApi, get_evg_api())
        binder.bind(MongoWrapper, get_mongo_wrapper())
    inject.configure_once(dependencies)

    return app
