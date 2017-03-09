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

import os
import pickle
import threading
import time

from flask.globals import request
from flask.wrappers import Response

from rapid.client.communicator.ClientCommunicator import ClientCommunicator
from rapid.lib import api_key_required
from rapid.lib.StoreService import StoreService
from rapid.lib.Utils import UpgradeUtil
from rapid.lib.WorkRequest import WorkRequest
from ..executor.Executor import Executor
from ...lib.BaseController import BaseController
from ...lib.Version import Version
import logging

logger = logging.getLogger("rapid")

try:
    import uwsgi
except:
    pass


class WorkController(BaseController):
    executors = []

    def register_url_rules(self, flask_app):
        """
        This is the entry point for the controller. All URL ruls are add_url_rule(d) here.
        :param flask_app: The app you want to add a url to
        :return: void
        """
        flask_app.add_url_rule('/work/request', 'work_request', api_key_required(self.work_request))
        flask_app.add_url_rule('/work/execute', 'work_execute', api_key_required(self.work_execute), methods=['POST'])
        self.app = flask_app

    def work_request(self):
        current_work = StoreService.get_executors()
        current_work = current_work + self.__get_quarantined_items()
        work = {'current_work': current_work,
                'hostname': self.app.rapid_config.hostname}
        if self.can_work_on() and self.check_version(request):
            return Response(json.dumps(work), content_type='application/json', headers={Version.HEADER: Version.get_version()})
        return Response(json.dumps(work), status=423, content_type='application/json', headers={Version.HEADER: Version.get_version()})

    def __get_quarantined_items(self):
        items = []
        quarantine_directory = self.app.rapid_config.quarantine_directory
        if quarantine_directory:
            communicator = None
            if not os.path.isdir(quarantine_directory):
                os.makedirs(quarantine_directory)

            for item in os.listdir(quarantine_directory):
                if item in ['.', '..']:
                    continue
                try:
                    items.append({'action_instance_id': int(item), 'pid': 'quarantined'})
                    if communicator is None:
                        communicator = ClientCommunicator(self.app.rapid_config.master_uri,
                                                          self.app.rapid_config.quarantine_directory,
                                                          verify_certs=self.app.rapid_config.verify_certs,
                                                          get_files_auth=self.app.rapid_config.get_files_basic_auth)
                    try:
                        delete_file = False
                        with open("{}/{}".format(quarantine_directory, item), 'r') as file:
                            data = pickle.loads(file.read())
                            try:
                                status = data['status']
                                parameters = data['parameters'] if 'parameters' in data else None
                                stats = data['stats'] if 'stats' in data else None
                                results = data['results'] if 'results' in data else None

                                communicator.send_done(int(item), status, parameters, stats, results, logger, headers={'X-Rapid-Quarantine': 'true'})
                                delete_file = True
                            except:
                                import traceback
                                traceback.print_exc()
                                pass

                        if delete_file:
                            try:
                                os.remove("{}/{}".format(quarantine_directory, item))
                            except:
                                logger.error("Couldn't remove.")
                    except:
                        import traceback
                        traceback.print_exc()
                        pass

                except:
                    pass
        return items

    def can_work_on(self, work=None):
        """
        This checks the work queue and what is being run at the moment.
        :param work
        :type work dict
        :return: True|False
        """
        executors = StoreService.get_executors()
        return len(executors) < self.app.rapid_config.executor_count and not self.currently_running(work)

    def currently_running(self, work):
        pid_exists = False

        try:
            if work['action_instance_id'] is not None:
                pid_exists = StoreService.check_for_pidfile(work['action_instance_id'])
                if pid_exists:
                    logger.info("Request was sent, but was already running, ignoring for [{}]".format(work['action_instance_id']))
        except:
            pass

        return pid_exists

    def check_version(self, check_request):
        if Version.HEADER in check_request.headers:
            if check_request.headers[Version.HEADER] == self.get_version():
                return True
            else:
                if not StoreService.is_updating(self.app):
                    StoreService.set_updating(self.app)
                    updating = True
                    thread = threading.Thread(target=self._perform_upgrade, args=(check_request.headers[Version.HEADER],))
                    thread.daemon = True
                    thread.start()

                return False

        return False

    def _perform_upgrade(self, new_version):
        logger.info("Performing upgrade: {}".format(new_version))

        executors = self._sleep_for_executors()
        self._start_upgrade(new_version, executors)

    def _start_upgrade(self, new_version, executors):
        if len(executors) == 0:
            UpgradeUtil.upgrade_version(new_version, self.app.rapid_config)
        else:
            logger.info("Waiting for executors...")
            StoreService.set_updating(self.app, False)

    @staticmethod
    def _sleep_for_executors(seconds_to_sleep=10, count_limit=10):
        executors = StoreService.get_executors()
        count = 0
        while len(executors) != 0:
            time.sleep(seconds_to_sleep)
            count += 1
            if count >= count_limit:
                break
            executors = StoreService.get_executors()
        return executors

    def get_version(self):
        return Version.get_version()

    def work_execute(self):
        try:
            if self.can_work_on(request.get_json()):
                self.start_work()
                executors = StoreService.get_executors()
                headers = {}
                if len(executors) + 1 >= self.app.rapid_config.executor_count:
                    headers["X-Exclude-Resource"] = 'true'
                return Response(json.dumps({"message": "Work started"}), status=201, content_type="application/json", headers=headers)
        except Exception as exception:
            logger.error(exception)
            return Response(json.dumps({'message': exception.message}), status=422, content_type='application/json')

        return Response(json.dumps({"message": "Cannot execute work at this time."}), status=423, content_type='application/json')

    def start_work(self):
        executor = Executor(WorkRequest(json.loads(request.get_json())),
                            self.app.rapid_config.master_uri,
                            workspace=self.app.rapid_config.workspace,
                            quarantine=self.app.rapid_config.quarantine_directory,
                            verify_certs=self.app.rapid_config.verify_certs,
                            rapid_config=self.app.rapid_config)
        executor.verify_work_request()
        executor.start()
