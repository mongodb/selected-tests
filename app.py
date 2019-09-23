"""
Application to serve API of selected-tests service.
"""

from flask import Flask


def create_app() -> Flask:
    """
    Create an instance of the flask application.

    :return: Instance of flask application.
    """
    app = Flask(__name__)

    @app.route('/health')
    def health():
        """
       Get information about whether service is running
       """
        return 'ok'

    return app


if __name__ == '__main__':
    create_app().run(host='0.0.0.0', port=8080)
