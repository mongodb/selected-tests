# Contributing / Development

## External Contributors

TBD.

## Development tools

We use a number of python tools to support development:
 * [black](https://github.com/psf/black) for formatting
 * [pydocstyle](https://github.com/PyCQA/pydocstyle) 
 * [pytest](https://docs.pytest.org/en/latest/)
 * [flake8](https://flake8.pycqa.org/en/latest/)
 * [isort](https://github.com/timothycrosley/isort)
 * [mypy](https://github.com/timothycrosley/isort)
 
## Testing/Formatting/Linting

You can use the following commands to ensure that the code passes all tests and checks:
 
```
$ poetry run pytest --flake8 --isort --junitxml=test_output_junit.xml
$ poetry run black --check --diff src tests
$ poetry run pydocstyle src
$ poetry run pytest --mypy src
```

To get code coverage information, you can run pytest directly.
```
$ poetry run pytest --cov=src --cov-report=html
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
