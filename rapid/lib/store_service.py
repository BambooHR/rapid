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
# pylint: disable=broad-except,protected-access
import os
import logging
import tempfile

import jsonpickle

from rapid.lib.in_memory_store import InMemoryStore

logger = logging.getLogger("rapid")

try:
    import uwsgi
except ImportError:
    uwsgi = InMemoryStore()


class StoreService(object):

    @staticmethod
    def get_executors():
        executors = []
        try:
            tmp_dir = tempfile.gettempdir()
            for filename in os.listdir(tmp_dir):
                try:
                    _sp = filename.split('-')
                    if _sp[0] == 'rapid':
                        try:
                            os.kill(int(_sp[2]), 0)
                            executors.append({'action_instance_id': _sp[1], 'pid': _sp[2]})
                        except OSError:
                            os.remove(os.path.join(tmp_dir, filename))
                except Exception:
                    pass
        except Exception as exception:
            logger.exception(exception)
        return executors

    @staticmethod
    def _get_tempfile_name(executor):
        return os.path.join(tempfile.gettempdir(), "rapid-{}-{}".format(executor.work_request.action_instance_id, executor.pid))

    @staticmethod
    def clear_executor(executor):
        try:
            os.remove(StoreService._get_tempfile_name(executor))
        except OSError:
            pass

    @staticmethod
    def save_executor(executor):
        try:
            with open(StoreService._get_tempfile_name(executor), 'w') as file_out:
                file_out.write("{}".format(executor.pid))
        except IOError as exception:
            logger.exception(exception)

    @staticmethod
    def save_clients(clients, app):
        try:
            uwsgi.cache_update("_rapidci_clients", jsonpickle.dumps(clients))
        except (AttributeError, NameError) as exception:
            logger.exception(exception)
            app.rapid_config.clients = clients

    @staticmethod
    def get_clients(app):
        """
        :param app:
        :type app:
        :return:
        :rtype: dict
        """
        try:
            return jsonpickle.loads(StoreService.get_key('_rapidci_clients'))
        except Exception:
            if not hasattr(app.rapid_config, 'clients'):
                app.rapid_config.clients = {}
            return app.rapid_config.clients

    @staticmethod
    def save_master_key(app, api_key):  # pylint: disable=unused-argument
        return StoreService.__set_key('_rapidci_master_key', jsonpickle.dumps(api_key))

    @staticmethod
    def get_master_key(app):
        try:
            return jsonpickle.loads(uwsgi.cache_get("_rapidci_master_key"))
        except Exception:
            return app.rapid_config._rapidci_master_key if hasattr(app.rapid_config, "_rapidci_master_key") else None

    @staticmethod
    def set_updating(app, updating=True):
        try:
            uwsgi.cache_update("_rapidci_updating", jsonpickle.dumps(updating))
        except Exception:
            app.rapid_config._rapidci_updating = updating

    @staticmethod
    def is_updating(app):
        try:
            return jsonpickle.loads(StoreService.get_key('_rapidci_updating'))
        except Exception:
            return app.rapid_config._rapidci_updating if hasattr(app.rapid_config, "_rapidci_updating") else False

    @staticmethod
    def check_for_pidfile(action_instance_id):
        try:
            pid_name = 'rapid-{}'.format(action_instance_id)
            for filename in os.listdir(tempfile.gettempdir()):
                if pid_name in filename:
                    return filename
        except OSError:
            pass
        return None

    @staticmethod
    def is_completing(action_instance_id):
        return StoreService.__is_by_key("_completing_{}".format(action_instance_id), 'true')

    @staticmethod
    def set_completing(action_instance_id):
        return StoreService.__set_key('_completing_{}'.format(action_instance_id), 'true')

    @staticmethod
    def clear_completing(action_instance_id):
        return StoreService.__clear_key("_completing_{}".format(action_instance_id))

    @staticmethod
    def set_calculating_workflow(pipeline_instance_id):
        return StoreService.__set_key('_calculating_{}'.format(pipeline_instance_id), "true")
        
    @staticmethod
    def is_calculating_workflow(pipeline_instance_id):
        return StoreService.__is_by_key('_calculating_{}'.format(pipeline_instance_id), 'true')

    @staticmethod
    def clear_calculating_workflow(pipeline_instance_id):
        return StoreService.__clear_key('_calculating_{}'.format(pipeline_instance_id))

    @staticmethod
    def __is_by_key(key, value):
        try:
            return value == StoreService.get_key(key)
        except Exception:
            pass
        return False

    @staticmethod
    def __set_key(key, value):
        try:
            uwsgi.cache_update(key, value)
            return True
        except Exception:
            pass
        return False

    @staticmethod
    def __clear_key(key):
        try:
            uwsgi.cache_del(key)
            return True
        except Exception:
            logger.info("FAILED TO clear cache-key: {}".format(key))
        return False

    @staticmethod
    def get_key(key):
        try:
            return uwsgi.cache_get(key)
        except Exception:
            return None
