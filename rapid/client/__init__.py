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

try:
    import simplejson as json
except:
    import json

import logging
import os
import threading
from flask import Flask
import time
from ..lib import setup_config_from_file
from .communicator.ClientCommunicator import ClientCommunicator
from .controllers import register_controllers

app = Flask("rapidci_client")
app.rapid_config = {'_is': 'client'}
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

logger = logging.getLogger("rapid")
logger.addHandler(handler)
logger.setLevel(logging.INFO)


UWSGI = None
try:
    import uwsgi
    UWSGI = True
except ImportError:
    pass


@app.route('/status')
def status():
    return "Running"

@app.errorhandler(500)
def internal_error(exception):
    response = json.dumps(exception.to_dict())
    response.status_code = exception.status_code
    response.content_type = 'application/json'
    return response

def configure_application(flask_app, args):
    setup_config_from_file(flask_app, args)
    register_controllers(flask_app)
    if (UWSGI and 1 == uwsgi.worker_id()) or UWSGI is None:
        setup_client_register_thread()
        clean_workspace()

def clean_workspace():
    try:
        import shutil
        if os.path.isdir(app.rapid_config.workspace):
            shutil.rmtree(app.rapid_config.workspace)
        os.mkdir(app.rapid_config.workspace)
    except:
        pass

def _registration_thread():
    communicator = ClientCommunicator(app.rapid_config.master_uri, app.rapid_config.quarantine_directory, app, app.rapid_config.verify_certs)
    while True:
        communicator.register(app.rapid_config)
        time.sleep(app.rapid_config.registration_rate)

def setup_client_register_thread():
    logger.info("Setting up client register thread")
    thread = threading.Thread(target=_registration_thread)
    thread.daemon = True
    thread.start()
