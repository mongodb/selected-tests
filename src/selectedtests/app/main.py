"""Application to serve API of selected-tests service."""
from werkzeug.middleware.proxy_fix import ProxyFix
from selectedtests.app.controllers import *

from selectedtests.app.app import app

DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT = 8080

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # type: ignore


if __name__ == "__main__":
    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT)
