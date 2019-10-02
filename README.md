# Selected Tests

This service is used to predict which tests need to run based on code changes.

# Set up environment
```
pip install -r requirements.txt
pip install -e .
```

# Run app locally
```
python src/selectedtests/app/app.py
```

# Run tests
Testing is done via pytest. You can pass the --flake8 argument to perform some
flake8 sanity checks on .py files.
```
pytest --flake8 -c pyproject.toml
```

To get code coverage information, you can run pytest directly.
```
$ pytest --cov=src --cov-report=html
```

# Pushing to staging
The staging environment for this service is
[here](https://selected-tests.server-tig.prod.corp.mongodb.com/swagger). In order to test your
changes there, make a pr with your branch and make sure it passes the required evergreen tests. Then, 
push your changes to the remote 'staging' branch. 

That command will look something like this if your branch is called 'new_branch'
 and the original selected-tests repo is called origin:
```
git push origin new_branch:origin/staging
```

## Style

This project is formatting with [black](https://github.com/psf/black). To autoformat your code, you
can use the black command line tool:

```
$ black src tests --config setup.cfg
```

See the black [documentation](https://github.com/psf/black#editor-integration) for details on how
to configure your editor to automatically format your code.

##Swagger

The swagger documentation for this service can be found at the /swagger endpoint. If running
locally, navigate to http://localhost:8080/swagger to see it.

If any new endpoints are added to the service or if the service is updated in such a way that any of
the existing endpoints' contracts change, the swagger documentation must be updated to reflect the
new state of the service before that change can be merged to master.

Documentation for how the swagger documentation is done can be found 
[here](https://flask-restplus.readthedocs.io/en/stable/swagger.html).

## Deploy

Deployment is done via helm to [kanopy](https://github.com/10gen/kanopy-docs#index). The project
will automatically be deployed on merge to master. The deployed application will be at
http://selected-tests.server-tig.prod.corp.mongodb.com .
