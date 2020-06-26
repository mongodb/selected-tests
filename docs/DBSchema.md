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
// Find all the source files related to a given task. In this query, source files are returned for the task "change_streams"
> db.task_mappings_tasks.aggregate({$match:{name:'change_streams'}}, {$lookup:{from:'task_mappings', localField:'task_mapping_id', foreignField:'_id', as: 'tasks'}}, {$unwind:'$tasks'}, {$sort: {'tasks.source_file': 1}}, {$group:{_id:'$name', source_files:{$push:'$tasks.source_file'}}}, {$project:{task_name:'$_id', source_files:1, _id:0}}).toArray()[0]
{
        "source_files" : [
                "src/mongo/db/catalog/rename_collection.cpp",
                "src/mongo/db/catalog/rename_collection.cpp",
                "src/mongo/s/config_server_catalog_cache_loader.cpp"
        ],
        "task_name" : "change_streams"
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
