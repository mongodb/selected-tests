from flask import Flask

from selectedtests.app.swagger_api import Swagger_Api
from selectedtests.helpers import get_evg_api, get_mongo_wrapper

evg_api = get_evg_api()
mongo = get_mongo_wrapper()

app = Flask(__name__)
api = Swagger_Api(
        app,
        version="1.0",
        title="Selected Tests Service",
        description="This service is used to predict which tests need to run based on code changes",
        doc="/swagger",
    )