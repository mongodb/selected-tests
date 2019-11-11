"""Application to serve API of selected-tests service."""
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
from evergreen.api import EvergreenApi

from selectedtests.app.swagger_api import Swagger_Api
from selectedtests.app.controllers.health_controller import add_health_endpoints
from selectedtests.app.controllers.project_test_mappings_controller import (
    add_project_test_mappings_endpoints,
)
from selectedtests.app.controllers.project_task_mappings_controller import (
    add_project_task_mappings_endpoints,
)
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.helpers import get_evg_api, get_mongo_wrapper

DEFAULT_PORT = 8080


def create_app(mongo: MongoWrapper, evg_api: EvergreenApi) -> Flask:
    """
    Create an instance of the flask application.

    :param mongo: Mongo Wrapper instance
    :param evg_api: An instance of the evg_api client
    :return: Instance of flask application.
    """
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    api = Swagger_Api(
        app,
        version="1.0",
        title="Selected Tests Service",
        description="This service is used to predict which tests need to run based on code changes",
        doc="/swagger",
    )

    add_health_endpoints(api)
    add_project_test_mappings_endpoints(api, mongo, evg_api)
    add_project_task_mappings_endpoints(api, mongo, evg_api)

    return app


def main():
    """Run the server."""
    mongo = get_mongo_wrapper()
    evg_api = get_evg_api()
    return create_app(mongo, evg_api)


if __name__ == "__main__":
    main().run(host="0.0.0.0", port=DEFAULT_PORT)
