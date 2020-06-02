# Client Configuration

Rapid runs on a pretty simple configuration. The Master and the Client have separate configurations. We will be
addressing the client configuration in this document. You can also combine the master and client configurations
into the same physical file.

Each configuration is a traditional python configuration using an `ini` format. There are groupings and key value
pairs per grouping. The defaults in the following definitions, are after the key and defined by a [].

## [client]
- port: [8081] - The port the client will listen to. 
- workspace: [`/tmp/rapid/workspace`] - This is the directory where scripts will be based. When running, their home will be this workspace.
- master_uri: [http://localhost:8080] - This is the master uri the client will attach to.
- registration_rate: [180] - In Seconds, how often the client will re-register with the master.
- executor_count: [2] - How many total parallel processes the client can run.
- grains: [] - The identifying type of work the client can run. There can be multiple grains separated by `;`. If blank, all work can run on this client.
- grain_restrict: [False] - As a boolean, if this is True, then it will require that the grain much match, and no wilcards can be set.
- quarantine_directory: [`/tmp/rapid/quarantine`] - If a client reports back, and the master is down, the job is quarantined and sent back when 
  the master is running again.  
- register_api_key: [None] - The registration api key required to register with the master.
- api_key: [random_seed] - The API Key required to communicate with the client.
- install_uri: [https://pypi.python.org/pypi/] - An override used to install client builds from.
- install_options: [] - Additional options for pip when installing.
- get_files_basic_auth: [None] - Basic auth in the form of `user:pass` in order to get the files from the master server.

## [general]
- use_ssl: [False] - Used to tell the master server to use SSL when communicating with this client.
- verify_certs: [True] - Used to override when using self-signed certificates, set to False.
- log_file: [None] - What log file to write to. 
