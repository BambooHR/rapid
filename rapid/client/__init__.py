"""
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
"""
import logging
import os
import threading
import time

try:
    import simplejson as json
except ImportError:
    import json

from flask import Flask

from rapid.lib import is_primary_worker, setup_logging, setup_status_route
from .parsers import load_parsers
from ..lib import setup_config_from_file
from .communicator.client_communicator import ClientCommunicator
from .controllers import register_controllers

app = Flask("rapidci_client")
app.rapid_config = {'_is': 'client'}
logger = logging.getLogger("rapid")


@app.errorhandler(500)
def internal_error(exception):
    response = json.dumps(exception.to_dict())
    response.status_code = exception.status_code
    response.content_type = 'application/json'
    return response


def setup_logger(flask_app):
    setup_logging(flask_app)


def configure_application(flask_app, args):
    setup_status_route(flask_app)
    setup_config_from_file(flask_app, args)
    setup_logger(flask_app)
    load_parsers()
    register_controllers(flask_app)
    if is_primary_worker() and not args.run and not args.upgrade:
        setup_client_register_thread()
        clean_workspace()

    if args.mode_logging:
        from rapid.lib.log_server import LogServer
        log_server = LogServer(args.log_dir)
        log_server.configure_application(flask_app)


def clean_workspace():
    try:
        import shutil
        if os.path.isdir(app.rapid_config.workspace):  # pylint: disable=no-member
            shutil.rmtree(app.rapid_config.workspace)  # pylint: disable=no-member
        os.mkdir(app.rapid_config.workspace)  # pylint: disable=no-member
    except Exception:  # pylint: disable=broad-except
        pass


def _registration_thread():
    communicator = ClientCommunicator(app.rapid_config.master_uri, app.rapid_config.quarantine_directory, app, app.rapid_config.verify_certs)  # pylint: disable=no-member
    while True:
        communicator.register(app.rapid_config)
        time.sleep(app.rapid_config.registration_rate)  # pylint: disable=no-member


def setup_client_register_thread():
    logger.info("Setting up client register thread")
    thread = threading.Thread(target=_registration_thread)
    thread.daemon = True
    thread.start()


def run_action_instance(action_instance_id):
    # type: (int) -> None
    from rapid.client.action_instance_runner import ActionInstanceRunner
    runner = ActionInstanceRunner(app.rapid_config)
    runner.run_action_instance(app, action_instance_id)


def upgrade_rapid():
    from rapid.client.client_upgrader import ClientUpgrader
    upgrader = ClientUpgrader(app.rapid_config)
    upgrader.upgrade(app)
