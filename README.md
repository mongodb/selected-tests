# Selected Tests

This service is used to predict which tests need to run based on code changes.

# Set up environment
```
pip install -r requirements.txt
pip install -e .
```

# Run app locally
```
python src/app.py
```

# Run tests
Testing is done via pytest. You can pass the --flake8 argument to perform some
flake8 sanity checks on .py files.
```
pytest --flake8
```

To get code coverage information, you can run pytest directly.
```
$ pytest --cov=src --cov-report=html
```

## Style

This project is formatting with [black](https://github.com/psf/black). To autoformat your code, you
can use the black command line tool:

```
$ black src
```

See the black [documentation](https://github.com/psf/black#editor-integration) for details on how
to configure your editor to automatically format your code.

## Deploy

Deployment is done via helm to [canopy](https://github.com/10gen/kanopy-docs#index). The project
will automatically be deployed on merge to master. The deployed application will be at
http://selected-tests.server-tig.prod.corp.mongodb.com .
