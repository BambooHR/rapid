# Master Configuration

Rapid runs on a pretty simple configuration. The Master and the Client have separate configurations. We will be
addressing the master configuration in this document.

Each configuration is a traditional python configuration using an `ini` format. There are groupings and key value
pairs per grouping. The defaults in the following definitions, are after the key and defined by a [].

## [master] grouping

- port: [8080] - The port the server should be listening on.
- queue_time: [6] - In seconds, how often the queue process will check the queue for work.
- db_connect_string: [] - The connection string to connect to the database. Please refer to [SQLAlchemy](https://docs.sqlalchemy.org/en/13/core/engines.html) documentation
  for the valid string format.
- queue_manager: [True] - Whether this master server should be running the queue
- queue_consider_late_time: [10] - In minutes, when should we start checking if a task is hung or not.
- register_api_key: [random_seed] - This is the api_key required to register the client with the master.
- api_key: [random_seed_2] - This is the api_key required to talk to the master from the client.
- github_user: [None] - The github user to interact with github and record statuses.
- github_pass: [None] - The password to interact with github and record statuses.
- github_webhooks_key: [None] - The key used for github webhooks signing.
- github_default_parameters [None] - A List, in yaml, newline separated and indented, list of key values to map to parameters in your pipelines.
  i.e. For a post of {'repository': {'key': 'foo'}} you put: `repository:repository.key` to set the parameter `repository` to `foo` in order
  for it to be available in environment variables in your scripts.
- custom_reports_dir: [None] - You can create custom reports for rapid, this is the directory that holds those reports.
- static_file_directory: [None] - The static directory for serving up your scripts.     
- basic_auth: [None] - The basic auth `user:pass` for serving up the static files from the static_file_directory.

## [general] grouping

- install_uri: [https://pypi.python.org/pypi/] - If you want to have a custom pypi server from which you grab the latest builds of rapid,
  you can do so with the option.
- install_options: [''] - Any additional options you a want to add to pip install.
- verify_certs: [True] - You can use verify_certs to be turned off when communicating with clients if you use custom self-signed certificates.
- log_file: [None] - Where to write logs to.

## [ecs] grouping
- ecs_config_file: [None] - When using the Amazon ECS option, you can specify the ECS Configuration file. 
