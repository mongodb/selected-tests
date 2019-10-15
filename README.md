# Selected Tests

This service is used to predict which tests need to run based on code changes.

## Set up environment
```
pip install -r requirements.txt
pip install -e .
```

## Run app locally
```
python src/selectedtests/app/app.py
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
