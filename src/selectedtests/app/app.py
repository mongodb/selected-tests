"""
Application to serve API of selected-tests service.
"""

from flask import Flask
from flask_restplus import Api

from selectedtests.app.controllers.health_controller import add_health_endpoints

DEFAULT_PORT = 8080


def create_app() -> Flask:
    """
    Create an instance of the flask application.

    :return: Instance of flask application.
    """
    app = Flask(__name__)
    api = Api(
        app,
        version="1.0",
        title="Selected Tests Service",
        description="This service is used to predict which tests need to run based on code changes",
        doc="/swagger"
    )

    add_health_endpoints(api)

    return app


def main():
    """Run the server."""
    return create_app()


if __name__ == "__main__":
    main().run(host="0.0.0.0", port=DEFAULT_PORT)
