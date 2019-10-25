# Selected Tests

This service is used to predict which tests need to run based on code changes.

## Set up environment
```
pip install -r requirements.txt
pip install -e .
```

## Run app locally

#### Prerequisites
- Evergreen credentials
  - You can find your credentials in your User Settings in the Evergreen UI. The cli looks for them
  in the usual default location, i.e. '~/.evergreen.yml'
```
python src/selectedtests/app/app.py
```

## Create task mappings
The task mapping cli command has only one required argument - the name of an evergreen project.
In order to run it, run the below.
```
task-mappings create EVERGREEN_PROJECT_NAME
```
Currently, it can only analyze public git repos. Private repo support is coming in a future version.

Its options are described below.
```
  --verbose                       Show logs.

  --start TEXT                    The date to begin analyzing the project at - has to be an iso date.
                                  Example: 2019-10-11T19:10:38
                                  [required]

  --end TEXT                      The date to stop analyzing the project at - has to be an iso date.
                                  Example: 2019-10-11T19:10:38
                                  [required]

  --source-file-regex TEXT        Regex to determine what files mappings will be created for.
                                  Example: '^src/mongo'
                                  [required]

  --module-name TEXT              The name of the associated module that should be analyzed.
                                  Example: enterprise

  --module-source-file-regex TEXT Regex to determine what module files mappings will be created for.
                                  Example: '^src'
                                  [required if module-name is non-empty]

  --output-file TEXT              Path to a file where the task mappings should be written to.
                                  Example: 'output.txt'

  --help                          Show this message and exit.
```

## Create test mappings
The test mapping cli command has only one required argument - the name of an evergreen project.
In order to run it, run the below.
```
test-mappings create EVERGREEN_PROJECT_NAME
```

Its options are described below.
```
  --verbose                       Show logs.

  --start TEXT                    The date to begin analyzing the project at - has to be an iso date.
                                  Example: 2019-10-11T19:10:38
                                  [required]

  --end TEXT                      The date to stop analyzing the project at - has to be an iso date.
                                  Example: 2019-10-11T19:10:38
                                  [required]

  --source-file-regex TEXT        Regex to determine which source files the mappings will be created for.
                                  Example: '^src/mongo'
                                  [required]

  --test-file-regex TEXT          Regex to determine which test files the mappings will be created for.
                                  Example: '^jstests.*'
                                  [required]

  --module-name TEXT              The name of the associated module that should be analyzed.
                                  Example: enterprise

  --module-source-file-regex TEXT Regex to determine which module souce files the mappings will be created for.
                                  Example: '^src'
                                  [required if module-name is non-empty]

  --module-test-file-regex TEXT   Regex to determine what module test files the mappings will be created for.
                                  Example: '^jstests'
                                  [required if module-name is non-empty]

  --output-file TEXT              Path to a file where the task mappings should be written to.
                                  Example: 'output.txt'

  --help                          Show this message and exit.
```


## Run tests
Testing is done via pytest. You can pass the --flake8 argument to perform some
flake8 sanity checks on .py files.
```
pytest --flake8 -c pyproject.toml
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

## Style

This project is formatting with [black](https://github.com/psf/black). To autoformat your code, you
can use the black command line tool:

```
$ black src tests
```

See the black [documentation](https://github.com/psf/black#editor-integration) for details on how
to configure your editor to automatically format your code.

### Pydoc

This project is checked with [pydocstyle](https://github.com/PyCQA/pydocstyle). This ensures that best
practices for pydoc's are followed and that every function and class has a pydoc associated with it.

In order to run it locally, run
```
pydocstyle src
```

## Swagger

The swagger documentation for this service can be found at the /swagger endpoint. If running
locally, navigate to http://localhost:8080/swagger to see it.

If any new endpoints are added to the service or if the service is updated in such a way that any of
the existing endpoints' contracts change, the swagger documentation must be updated to reflect the
new state of the service before that change can be merged to master.

Documentation for how the swagger documentation is done can be found
[here](https://flask-restplus.readthedocs.io/en/stable/swagger.html).

## Deploy

Deployment is done via helm to [Kanopy](https://github.com/10gen/kanopy-docs#index) (MongoDB
internal service). The project will automatically be deployed on merge to master. The deployed
application can be accessed at
https://selected-tests.server-tig.prod.corp.mongodb.com/health (MongoDB internal
app, see Authentication section for access).

# Selected Tests API
The selected-tests API is hosted internally at MongoDB. For this reason we restrict access to
engineers who are authenticated through CorpSecure (MongoDB's Single Sign On solution for internal
apps).

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
