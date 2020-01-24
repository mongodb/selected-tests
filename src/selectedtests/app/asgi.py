from selectedtests.app.app import create_app
from selectedtests.helpers import get_evg_api, get_mongo_wrapper

app = create_app(get_mongo_wrapper(), get_evg_api())
