"""Application to serve API of selected-tests service."""
from evergreen import EvergreenApi
from fastapi import FastAPI

from selectedtests.app.controllers import health_controller, project_task_mappings_controller, project_test_mappings_controller
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.helpers import get_mongo_wrapper, get_evg_api


def create_app(mongo_wrapper: MongoWrapper = None, evg_api: EvergreenApi = None) -> FastAPI:
    app = FastAPI(__name__,
                  version="1.0",
                  title="Selected Tests Service",
                  description="This service is used to predict which tests need to run based on code changes.",
                  docs_url="/swagger",
                  )
    app.include_router(health_controller.router, tags=["health"])
    app.include_router(project_task_mappings_controller.router,
                       prefix="/projects/{project}/task-mappings",
                       tags=["projects"],
                       )
    app.include_router(project_test_mappings_controller.router,
                       prefix="/projects/{project}/test-mappings",
                       tags=["projects"],
                       )
    app.state.db = mongo_wrapper or get_mongo_wrapper()
    app.state.evg_api = evg_api or get_evg_api()
    return app
