"""Application to serve API of selected-tests service."""
from fastapi import FastAPI

from selectedtests.app.controllers import health_controller, project_task_mappings_controller, project_test_mappings_controller

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
