"""Application to serve API of selected-tests service."""
import uvicorn as uvicorn

from selectedtests.app.app import create_app
from selectedtests.helpers import get_evg_api, get_mongo_wrapper

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8080


if __name__ == "__main__":
    uvicorn.run(
        create_app(get_mongo_wrapper(), get_evg_api()), host=DEFAULT_HOST, port=DEFAULT_PORT
    )
