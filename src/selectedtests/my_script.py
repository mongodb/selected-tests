from selectedtests.evergreen_helper import get_version_on_date
from selectedtests.helpers import get_evg_api
from datetime import datetime, timedelta
import time

start = time.time()
evg_api = get_evg_api()
now = datetime.now()
after_date = now - timedelta(weeks=24)
version = get_version_on_date(evg_api, "mongodb-mongo-master", after_date)
end = time.time()
print(end - start)
