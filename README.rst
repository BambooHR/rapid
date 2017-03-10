Rapid Framework
===============

Rapid Framework is a tool for integrating Continuous Integration, Automatic Testing, Automatic Building and Continuous Deployment in a quality and
efficient manner.

Why Rapid?
----------

Rapid was built with ease and scalability in mind. There are various features which allow you to take control of your builds and know what is happening
at all times. Rapid makes your CI Solution infrastructure. It simply works.

Rapid was built to be small and efficient. Rapid is a layered system which allows you to be free to scale your infrastructure as needed. Rapid is the
only CI Solution that we know of that can build and release itself with no down time.

Have you ever used a system that runs out of memory? Ever have a client blow up and you can't recover? That doesn't happen with Rapid. Try it out!

Requirements
------------

Server - System that supports python. At least 60MB of RAM! That's it!
Client - System that supports python. At least 30MB of RAM! That's it!

Features
--------

- Multi Staged pipelines
- Parallel Workflows
- Sliced Actions
- Ability to track time for all parts of your build
- Re-run Action possibility
- Prioritized builds
- Interstitial Runs
- Targeted clients
- Distributed Logging
- Automatic upgrades
- 24/7 Uptime - Install a new version and restart in 200ms!
- Behavior Point Test Mapping
- UWSGI integration
- Massive Scaling
- Github Integration for handling webhooks
- Release Step Mapping and workflows
- External process integration and workflow

Installation
------------

.. code-block:: bash

  $ pip install rapid-framework


Options
-------

.. code-block:: bash

  $ rapid --help


usage: rapid [-h] [-f CONFIG_FILE] [-p PORT] [-m] [-c] [-l] [-d LOG_DIR]
             [-q QA_DIR] [--downgrade DB_DOWNGRADE] [--create_db]
             [--create_migration MIGRATE]

Rapid Framework client main control

optional arguments:
  -h, --help            show this help message and exit
  -f CONFIG_FILE, --config CONFIG_FILE
                        config file path
  -p PORT, --port PORT  Port for the master to listen on
  -m, --master          Master mode is default
  -c, --client          Client mode
  -l, --logging         Logging mode
  -d LOG_DIR, --log_dir LOG_DIR
                        Logging directory
  -q QA_DIR, --qa_dir QA_DIR
                        QA Dir
  --downgrade DB_DOWNGRADE
                        Downgrade db for alembic
  --create_db           Create initial db
  --create_migration MIGRATE
                        Create Migration for alembic

License
-------
Rapid is **licensed** under the **Apache 2.0 License**. The terms of the license are as follows:

..

  Copyright (c) 2015 Michael Bright and Bamboo HR LLC

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.