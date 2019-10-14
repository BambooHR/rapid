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
import threading
import time

from flask import Flask, Response

from rapid.master.data import run_db_downgrade, configure_db
from rapid.lib import setup_config_from_file, is_primary_worker, setup_status_route
from rapid.lib.framework.ioc import IOC
from .controllers import register_controllers
from .data import configure_data_layer, run_db_upgrades, create_revision

app = Flask("rapidci_master")
app.rapid_config = {'_is': 'master'}
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# app.logger.addHandler(handler)  # pylint: disable=no-member
# app.logger.setLevel(logging.INFO)  # pylint: disable=no-member

logger = logging.getLogger("rapid")
logger.addHandler(handler)  # pylint: disable=no-member
logger.setLevel(logging.INFO)  # pylint: disable=no-member


# pylint: disable=broad-except

# Debug Code for sniffing out nplus one code!
# try:
#     # app.config['NPLUSONE_LOGGER'] = logging.getLogger('app.nplusone')
#     app.config['NPLUSONE_LOG_LEVEL'] = logging.ERROR
#     app.config['NPLUSONE_RAISE'] = True
#     from nplusone.ext.flask_sqlalchemy import NPlusOne
#     NPlusOne(app)
# except Exception:
#     pass


@app.errorhandler(500)
def internal_error(exception):
    response = Response(status=500, content_type='application/json')
    response.data = _to_dict(exception)
    app.logger.error(exception.message)  # pylint: disable=no-member
    return response


def _to_dict(exception):
    _rv = dict()
    _rv['message'] = exception.message if hasattr(exception, 'message') else 'An exception has occurred'
    return _rv


def configure_application(flask_app, args, manual_db_upgrade=False):
    IOC.register_global('flask_app', flask_app)
    setup_config_from_file(flask_app, args)
    configure_db()
    configure_sub_modules(flask_app, args)
    configure_data_layer(flask_app)
    register_controllers(flask_app)
    setup_status_route(flask_app)

    if args.static_file_dir:
        flask_app.rapid_config.static_file_directory = args.static_file_dir

    if args.basic_auth:
        flask_app.rapid_config.set_basic_auth(args.basic_auth)

    if is_primary_worker() and not manual_db_upgrade:
        if args.db_downgrade:
            run_db_downgrade(flask_app, args.db_downgrade)
        else:
            run_db_upgrades(flask_app)
            setup_queue_thread(flask_app)


def create_migration_script(flask_app, migration):
    create_revision(flask_app, migration)


def configure_sub_modules(flask_app, args):  # pylint: disable=unused-argument
    logger.info("------- Searching for and starting modules --------")
    modules = {}
    logger.info("-- Registering IOC Globals")
    for name in ['ci', 'qa', 'release', 'workflow']:
        try:
            module = __import__("rapid.{}".format(name), fromlist=['configure_module', 'register_ioc_globals'])
            modules[name] = module
            module.register_ioc_globals(flask_app)
            logger.info("    Registered: {}".format(name))
        except Exception:
            import traceback
            traceback.print_exc()

    logger.info("-- Configuring modules")
    for name, item in modules.items():  # pylint: disable=unused-variable
        try:
            modules[name].configure_module(flask_app)
            logger.info("    Configured: {}".format(name))
        except Exception:
            import traceback
            traceback.print_exc()
            logger.warning("NOT LOADED! Module {} did not load.".format(name))

    logger.info("------- Done --------")


def setup_queue_thread(flask_app):
    if flask_app.rapid_config.queue_manager:
        import os
        logger.info("Setting up master queue thread: [{}]".format(os.getpid()))
        thread = threading.Thread(target=run_queue, args=[flask_app])
        thread.daemon = True
        thread.start()


def run_queue(flask_app):
    from rapid.lib.store_service import StoreService
    from rapid.workflow.queue import Queue
    with flask_app.app_context():
        queue = IOC.get_class_instance(Queue)  # type: Queue
        while True:
            clients = []
            try:
                clients = StoreService.get_clients(flask_app)
            except:
                pass

            try:
                queue.process_queue(clients)
            except Exception as exception:
                logger.error(exception)

            try:
                queue.verify_still_working(clients)
            except Exception as exception:
                logger.error(exception)

            try:
                queue.reconcile_pipeline_instances()
            except Exception as exception:
                logger.error(exception)

            filtered_clients = {name: client for name, client in clients.items() if not hasattr(client, 'no-longer-active')}

            if filtered_clients != clients:
                StoreService.save_clients(filtered_clients, flask_app)
            time.sleep(flask_app.rapid_config.queue_time)
