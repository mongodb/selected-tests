# Selected Tests

The Selected Tests service is used to predict which tests need to run based on code changes.

# Selected Tests API
The selected-tests API is hosted internally at MongoDB. For this reason we restrict access to
engineers who are authenticated through CorpSecure (MongoDB's Single Sign On solution for internal
apps).

## Swagger

The swagger documentation for this API can be found at the /swagger endpoint,
https://selected-tests.server-tig.prod.corp.mongodb.com/swagger. If running locally, navigate to
http://localhost:8080/swagger to see it.

If any new endpoints are added to the service or if the service is updated in such a way that any of
the existing endpoints' contracts change, the swagger documentation must be updated to reflect the
new state of the service before that change can be merged to master.

Documentation for how the swagger documentation is done can be found
[here](https://flask-restplus.readthedocs.io/en/stable/swagger.html).

## Authentication
To make requests to the selected-tests API you will need to include your CorpSecure auth_user and
auth_token cookies in your request.

If you do not authenticate, any API requests will return a 302 and redirect to the Google OAuth
sign in page.

To make an API request, follow the following steps:
1. Log into the selected-tests service by going to the following link in your
   browser and logging in:
   https://selected-tests.server-tig.prod.corp.mongodb.com/health
2. Get your personal auth_token and auth_user cookies for the
   https://selected-tests.server-tig.prod.corp.mongodb.com domain. (You can find
   these under the Application tab in Chrome console.)
![Cookies example](https://github.com/mongodb/selected-tests/blob/master/cookies_example.png "Cookies example")
3. Now you can make a curl request to the API using your auth_token and auth_user
   cookies:
 ```
 curl --verbose -H "Content-Type: application/json" --cookie
 "auth_user=< your auth_user >;auth_token=< your auth_token >"
 https://selected-tests.server-tig.prod.corp.mongodb.com/health
 ```

## Create task mappings
The task mapping cli command has only one required argument - the name of an evergreen project.
In order to run it, run the below.
```
task-mappings create EVERGREEN_PROJECT_NAME
```
Currently, it can only analyze public git repos. Private repo support is coming in a future version.

## Create test mappings
The test mapping cli command has only one required argument - the name of an evergreen project.
In order to run it, run the below.
```
test-mappings create EVERGREEN_PROJECT_NAME
```

### Commands

A cron job should run the `process-test-mappings` and `process-task-mappings` commands once every
day. This will gather the unprocessed test mapping create and task mapping create requests and
process them so that test and task mappings for those projects are added to the db.

```
$ work-items process-test-mappings
$ work-items process-task-mappings
```

A cron job will run daily to update the two models described above. The cron job
will look at all git commits and mainline patch builds from the previous day and
create new test mappings and task mappings respectively. The commands to do this
are as follows:
```
$ test-mappings update
$ task-mappings update
```

## Run app locally

### Set up environment
```
pip install -r requirements.txt
pip install -e .
```

#### Prerequisites
You will need to set your Evergreen credentials in environment variables because the application
and CLIs authenticate to Evergreen using $EVG_API_USER and $EVG_API_KEY. You can set these to the
values in your local ~/.evergreen.yml file. You will also need to set the location of a mongodb
instance in an environment variable called ```SELECTED_TESTS_MONGO_URI```:
```
export EVG_API_USER="<your evg api user>"
export EVG_API_KEY="<your evg api key>"
export SELECTED_TESTS_MONGO_URI="localhost:27017"
python src/selectedtests/app/app.py
```


## Testing/Formatting/Linting
```
pytest --flake8 --isort
black src tests
pydocstyle src
```

To get code coverage information, you can run pytest directly.
```
$ pytest --cov=src --cov-report=html
```

## Pushing to staging
The staging environment for this service is
[here](https://selected-tests.server-tig.staging.corp.mongodb.com). In order to test your
changes there, make a pr with your branch and make sure it passes the required evergreen tests. Then,
push your changes to the remote 'staging' branch.

That command will look something like this if your branch is called 'new_branch'
 and the original selected-tests repo is called origin:
```
git push origin new_branch:staging
```

## Merging code to master

Merges to the selected-tests repo should be done via the Evergreen [Commit Queue](https://github.com/evergreen-ci/evergreen/wiki/Commit-Queue).

When your PR is ready to merge, add a comment with the following:
```
evergreen merge
```

## Deploy

Deployment is done via helm to [Kanopy](https://github.com/10gen/kanopy-docs#index) (MongoDB
internal service). The project will automatically be deployed on merge to master. The deployed
application can be accessed at
https://selected-tests.server-tig.prod.corp.mongodb.com/health (MongoDB internal
app, see Authentication section for access).
