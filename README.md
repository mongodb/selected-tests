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

## Database Schema
The _selected_tests_ database consists of a number of interlocking collections.
* _project_config_: A collection to contain project descriptions and meta data (last commit seen,
regexs for files etc.).
```
> db.project_config.findOne()
{
	"_id" : ...,
	"project" : "mongodb-mongo-master",
	"task_config" : {
		"most_recent_version_analyzed" : "mongodb_mongo_master_d2c18cfec00f3a43815dc524df3912cfb1e0198a",
		"source_file_regex" : "^src/mongo",
		"build_variant_regex" : "^!",
		"module" : null,
		"module_source_file_regex" : null
	},
	"test_config" : {
		"most_recent_project_commit_analyzed" : "0076e5242f265776102b8f8e8526322715f4c5f1",
		"source_file_regex" : "^src/mongo",
		"test_file_regex" : "^jstests",
		"module" : null,
		"most_recent_module_commit_analyzed" : null,
		"module_source_file_regex" : null,
		"module_test_file_regex" : null
	}
}
```
* _task_mappings_queue_: A queue of work items for processing task_mappings.
```
> db.task_mappings_queue.findOne()
{
	"_id" : ...,
	"created_on" : ISODate("2020-02-13T10:38:58.740Z"),
	"project" : "mongodb-mongo-master",
	"source_file_regex" : "^src/mongo",
	"module" : null,
	"module_source_file_regex" : null,
	"build_variant_regex" : "^!",
	"start_time" : ISODate("2020-02-13T11:15:47.837Z"),
	"end_time" : ISODate("2020-02-13T11:22:27.322Z")
}
```
* _task_mappings_: The current task mappings.
```
> db.task_mappings.findOne()
{
	"_id" : ...,
	"source_file" : "src/mongo/executor/network_interface_mock.cpp",
	"branch" : "master",
	"project" : "mongodb-mongo-master",
	"repo" : "mongo",
	"source_file_seen_count" : 1
}
// Aggregate task_mappings and task_mappings_tasks into the shape exported by the API.
> db.task_mappings.aggregate({$match:{"source_file" : "src/mongo/executor/network_interface_mock.cpp"}}, {$lookup:{"from": "task_mappings_tasks", "localField": "_id",  "foreignField": "task_mapping_id", "as": "tasks" }}, {$project:{_id:0, 'tasks._id':0, 'tasks.task_mapping_id':0}}).pretty()
{
	"source_file" : "src/mongo/executor/network_interface_mock.cpp",
	"branch" : "master",
	"project" : "mongodb-mongo-master",
	"repo" : "mongo",
	"source_file_seen_count" : 1,
	"tasks" : [
		{
			"name" : "replica_sets_large_txns_format",
			"variant" : "enterprise-rhel-62-64-bit",
			"flip_count" : 1
		},
		{
			"name" : "replica_sets_large_txns_format_05_enterprise-rhel-62-64-bit",
			"variant" : "enterprise-rhel-62-64-bit",
			"flip_count" : 1
		}
	]
}
```
* _task_mappings_tasks_: The current task mappings tasks. Documents from this collection
are joined to the _task_mappings_ documents _tasks_ field through the source_file field.
```
> db.task_mappings_tasks.findOne()
{
	"_id" : ...,
	"name" : "replica_sets_large_txns_format",
	"task_mapping_id" : ...,
	"variant" : "enterprise-rhel-62-64-bit",
	"flip_count" : 1
}
```

* _test_mappings_queue_: A queue of work items for processing test_mappings.
```
> db.test_mappings_queue.findOne()
{
	"_id" : ...,
	"created_on" : ISODate("2020-02-11T14:11:48.952Z"),
	"project" : "mongodb-mongo-master",
	"source_file_regex" : "^src/mongo",
	"test_file_regex" : "^jstests",
	"module" : null,
	"module_source_file_regex" : null,
	"module_test_file_regex" : null,
	"start_time" : ISODate("2020-02-12T11:59:36.051Z"),
	"end_time" : ISODate("2020-02-12T12:02:14.782Z")
}
```
* _test_mappings_:  The current test mappings.
```
> db.test_mappings.find({"source_file" : "src/mongo/executor/network_interface_mock.cpp"}).pretty()
{
	"_id" : ...,
	"source_file" : "src/mongo/executor/network_interface_mock.cpp",
	"branch" : "master",
	"project" : "mongodb-mongo-master",
	"repo" : "mongo",
	"source_file_seen_count" : 2
}
// Aggregate test_mappings and test_mappings_test_files into the shape exported by the API.
> db.test_mappings.aggregate({$match:{"source_file" : "src/mongo/db/s/config/configsvr_create_database_command.cpp"}}, {$lookup:{"from": "test_mappings_test_files", "localField": "_id",  "foreignField": "test_mapping_id", "as": "test_files" }}, {$project:{_id:0, 'test_files._id':0, 'test_files.test_mapping_id':0}}).pretty()
{
	"source_file" : "src/mongo/db/s/config/configsvr_create_database_command.cpp",
	"branch" : "master",
	"project" : "mongodb-mongo-master",
	"repo" : "mongo",
	"source_file_seen_count" : 5,
	"test_files" : [
		{
			"name" : "jstests/core/views/views_validation.js",
			"test_file_seen_count" : 2
		}
	]
}

```
* _test_mappings_test_files_: The current test mappings test_files. Documents from this collection
are joined to _test_mappings_ documents  _test_files_ field through the source_file field.
```
> db.test_mappings_test_files.findOne({"source_file" : "src/mongo/db/s/config/configsvr_create_database_command.cpp"})
{
	"_id" : ...,
	"name" : "jstests/core/views/views_validation.js",
	"test_mpapping_id" : ...,
	"test_file_seen_count" : 2
}
```

### Analyze distrubution of thresholds
The distribution of the thresholds for test_mappings and task_mappings can be
seen by running the jupyter notebooks in the `notebooks` directory. To run
them, set the SELECTED_TESTS_MONGO_URI environment variable to the database you
would like to analyze and run jupyter notebooks:
```
export SELECTED_TESTS_MONGO_URI="localhost:27017"
poetry run jupyter notebook
```

## Create task mappings
The task mapping cli command has only one required argument - the name of an evergreen project.
In order to run it, run the below.
```
poetry run task-mappings create EVERGREEN_PROJECT_NAME
```
Currently, it can only analyze public git repos. Private repo support is coming in a future version.

## Create test mappings
The test mapping cli command has only one required argument - the name of an evergreen project.
In order to run it, run the below.
```
poetry run test-mappings create EVERGREEN_PROJECT_NAME
```

### Commands

A cron job should run the `process-test-mappings` and `process-task-mappings` commands once every
day. This will gather the unprocessed test mapping create and task mapping create requests and
process them so that test and task mappings for those projects are added to the db.

```
$ poetry run work-items process-test-mappings
$ poetry run work-items process-task-mappings
```

A cron job will run daily to update the two models described above. The cron job
will look at all git commits and mainline patch builds from the previous day and
create new test mappings and task mappings respectively. The commands to do this
are as follows:
```
$ poetry run test-mappings update
$ poetry run task-mappings update
```

## Run app locally

### Set up environment
[Install poetry](https://github.com/python-poetry/poetry#installation)

Install dependencies:
```
poetry install
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
uvicorn --host 0.0.0.0 --port 8080 --workers 1 selectedtests.app.asgi:app <--reload>
```
__Note__: reload is only used in development mode.

## Testing/Formatting/Linting
```
poetry run black src tests
poetry run pydocstyle src
poetry run pytest
```

To get code coverage information, you can run pytest directly.
# WIP
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
