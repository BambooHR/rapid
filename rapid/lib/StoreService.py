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

import os
import logging
import jsonpickle

logger = logging.getLogger("rapid")

try:
    import uwsgi
except ImportError:
    uwsgi = {}


class StoreService(object):

    @staticmethod
    def get_executors():
        executors = []
        try:
            for filename in os.listdir("/tmp"):
                try:
                    sp = filename.split('-')
                    if sp[0] == 'rapid':
                        try:
                            os.kill(int(sp[2]), 0)
                            executors.append({'action_instance_id': sp[1], 'pid': sp[2]})
                        except:
                            os.remove("/tmp/{}".format(filename))
                except:
                    pass
        except:
            import traceback
            traceback.print_exc()
            pass
        return executors

    @staticmethod
    def clear_executor(executor):
        try:
            os.remove("/tmp/rapid-{}-{}".format(executor.work_request.action_instance_id, executor.pid))
        except:
            pass

    @staticmethod
    def save_executor(executor):
        try:
            f = open('/tmp/rapid-{}-{}'.format(executor.work_request.action_instance_id, executor.pid), 'w')
            f.write("{}".format(executor.pid))
            f.close()
        except:
            import traceback
            traceback.print_exc()

    @staticmethod
    def save_clients(clients, app):
        try:
            uwsgi.cache_update("_rapidci_clients", jsonpickle.dumps(clients))
        except:
            import traceback
            traceback.print_exc()
            app.rapid_config.clients = clients

    @staticmethod
    def get_clients(app):
        try:
            return jsonpickle.loads(uwsgi.cache_get("_rapidci_clients"))
        except:
            if not hasattr(app.rapid_config, 'clients'):
                app.rapid_config.clients = {}
            return app.rapid_config.clients

    @staticmethod
    def save_master_key(app, api_key):
        try:
            uwsgi.cache_update("_rapidci_master_key", jsonpickle.dumps(api_key))
        except:
            app.rapid_config._rapidci_master_key = api_key

    @staticmethod
    def get_master_key(app):
        try:
            return jsonpickle.loads(uwsgi.cache_get("_rapidci_master_key"))
        except:
            return app.rapid_config._rapidci_master_key if hasattr(app.rapid_config, "_rapidci_master_key") else None

    @staticmethod
    def set_updating(app, updating=True):
        try:
            uwsgi.cache_update("_rapidci_updating", jsonpickle.dumps(updating))
        except:
            app.rapid_config._rapidci_updating = True

    @staticmethod
    def is_updating(app):
        try:
            return jsonpickle.loads(uwsgi.cache_get("_rapidci_updating"))
        except:
            return app.rapid_config._rapidci_updating if hasattr(app.rapid_config, "_rapidci_updating") else False

    @staticmethod
    def check_for_pidfile(action_instance_id):
        try:
            pid_name = 'rapid-{}'.format(action_instance_id)
            for filename in os.listdir("/tmp"):
                if pid_name in filename:
                    return True
        except:
            pass

    @staticmethod
    def is_completing(action_instance_id):
        try:
            return "true" == uwsgi.cache_get("_completing_{}".format(action_instance_id))
        except:
            pass
        return False

    @staticmethod
    def set_completing(action_instance_id):
        try:
            uwsgi.cache_update('_completing_{}'.format(action_instance_id), "true")
        except:
            pass

    @staticmethod
    def clear_completing(action_instance_id):
        try:
            uwsgi.cache_del("_completing_{}".format(action_instance_id))
            return True
        except:
            logger.info("FAILED TO clear_completing")
        return False
