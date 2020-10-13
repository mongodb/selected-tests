"""Application to serve API of selected-tests service."""
import traceback

import structlog

from evergreen import EvergreenApi
from fastapi import FastAPI
from miscutils.logging_config import Verbosity
from starlette.requests import Request
from starlette.responses import JSONResponse

from selectedtests.app.controllers import (
    health_controller,
    project_task_mappings_controller,
    project_test_mappings_controller,
)
from selectedtests.config.logging_config import config_logging
from selectedtests.datasource.mongo_wrapper import MongoWrapper

LOGGER = structlog.get_logger(__name__)


def log_exception(ex: Exception) -> None:
    """Log an exception that gets caught."""
    LOGGER.error(
        "An exception occurred during this request",
        exception=ex,
        stack_trace=traceback.format_exc(),
    )


def create_app(mongo_wrapper: MongoWrapper, evg_api: EvergreenApi) -> FastAPI:
    """
    Create a selected-tests REST API.

    :param mongo_wrapper: MongoDB wrapper.
    :param evg_api: Evergreen Api.
    :return: The application.
    """
    config_logging(verbosity=Verbosity.INFO, human_readable=False)

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
    app.state.db = mongo_wrapper
    app.state.evg_api = evg_api

    @app.exception_handler(Exception)
    async def uncaught_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all uncaught exceptions."""
        log_exception(exc)
        return JSONResponse(
            status_code=500,
            content={"message": "An unexpected exception occurred during this request"},
        )

    return app
