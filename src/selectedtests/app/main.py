"""Application to serve API of selected-tests service."""
import uvicorn as uvicorn

from selectedtests.app.app import create_app

DEFAULT_HOST="0.0.0.0"
DEFAULT_PORT = 8080


if __name__ == "__main__":
    uvicorn.run(create_app(), host=DEFAULT_HOST, port=DEFAULT_PORT)
