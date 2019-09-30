"""
Application to serve API of selected-tests service.
"""

from flask import Flask, jsonify

DEFAULT_PORT = 8080


def create_app() -> Flask:
    """
    Create an instance of the flask application.

    :return: Instance of flask application.
    """
    app = Flask(__name__)

    @app.route("/health")
    def health():
        """
        Get information about whether service is running
        """
        return jsonify({"online": True})

    return app


def main():
    """Run the server."""
    return create_app()


if __name__ == "__main__":
    main().run(host="0.0.0.0", port=DEFAULT_PORT)
