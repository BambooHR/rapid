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
import time
import jsonpickle
from flask import request, Response

from rapid.lib import api_key_required, json_response
from rapid.lib.constants import HeaderConstants
from rapid.lib.exceptions import HttpException, VcsNotFoundException
from rapid.lib.store_service import StoreService
from rapid.lib.version import Version
from rapid.master.communicator.client import Client
from rapid.master.communicator.master_communicator import MasterCommunicator
from rapid.workflow.action_dal import ActionDal

try:
    import simplejson as json
except ImportError:
    import json

# pylint: disable=broad-except


class UtilityRouter(object):

    def __init__(self, flask_app=None):
        self.flask_app = flask_app

    def register_url_rules(self):
        self.flask_app.add_url_rule('/clients/show', 'get_clients', api_key_required(self.show_clients))
        self.flask_app.add_url_rule('/client/register', 'register_client', self.register_client, methods=["POST"])
        self.flask_app.add_url_rule('/clients/working', 'get_clients_working', api_key_required(self.working_clients), methods=['GET'])
        self.flask_app.add_url_rule('/clients/<path:client_ip>/still_working/<path:action_instance_id>', 'client_still_working_on', api_key_required(self.client_still_working_on), methods=['GET'])
        self.flask_app.add_url_rule('/clients/verify_working', 'client_verify_working', api_key_required(self.client_verify_working), methods=['GET'])

        self.flask_app.register_error_handler(HttpException, self.http_exception_handler)
        self.flask_app.register_error_handler(VcsNotFoundException, self.http_exception_handler)

    def http_exception_handler(self, exception):
        response = Response(json.dumps(exception.to_dict()))
        response.status_code = exception.status_code
        response.content_type = 'application/json'
        return response

    @json_response()
    def client_still_working_on(self, client_ip, action_instance_id):
        clients = []
        try:
            clients = StoreService.get_clients(self.flask_app)
        except Exception:
            pass

        if client_ip in clients:
            return {'status': MasterCommunicator.is_still_working_on(action_instance_id, clients[client_ip], self.flask_app.rapid_config.verify_certs)}

        return {"status": "No client found"}

    @json_response()
    def client_verify_working(self):
        action_dal = ActionDal(None, None)
        return action_dal.get_verify_working(self.flask_app.rapid_config.queue_consider_late_time)

    def working_clients(self):
        clients = {}
        for client in MasterCommunicator.get_clients_working_on(StoreService.get_clients(self.flask_app).values(), self.flask_app.rapid_config.verify_certs):
            if client is not None:
                if client['version'] not in clients:
                    clients[client['version']] = []
                clients[client['version']].append(client)
        return Response(json.dumps(clients), content_type='application/json')

    def register_client(self):
        return self.register_request(request)

    def show_clients(self):
        return Response(jsonpickle.encode(self._get_clients()), content_type='application/json')

    def register_request(self, in_request):
        if 'Content-Type' in in_request.headers and in_request.headers['Content-Type'] == 'application/json':
            if 'X-Rapidci-Register-Key' in in_request.headers and in_request.headers['X-Rapidci-Register-Key'] == self.flask_app.rapid_config.register_api_key:
                remote_addr = in_request.remote_addr
                remote_port = in_request.headers['X-Rapidci-port'] if 'X-Rapidci-port' in in_request.headers else None
                time_elapse = max((time.time() * 1000) - float(in_request.headers['X-Rapidci-time']), 1) if 'X-Rapidci-time' in in_request.headers else None

                grains = in_request.json['grains'] if 'grains' in in_request.json else ''
                hostname = in_request.json['hostname'] if 'hostname' in in_request.json else 'unknown'
                grain_restrict = in_request.json['grain_restrict'] if 'grain_restrict' in in_request.json else False

                api_key = in_request.headers['X-Rapidci-Client-Key'] if 'X-Rapidci-Client-Key' in in_request.headers else False
                is_ssl = in_request.headers['X-Is-Ssl'].lower() == 'true' if 'X-is_ssl' in in_request.headers else False

                if remote_port == 443:
                    is_ssl = True

                if not api_key:
                    raise Exception("NO API KEY!")
                client = Client(remote_addr, int(remote_port), grains, grain_restrict, api_key, is_ssl, hostname, time_elapse)

                if HeaderConstants.SINGLE_USE not in in_request.headers:
                    self.store_client(remote_addr, client)

                return Response(jsonpickle.encode(client),
                                content_type='application/json', headers={'Content-Type': 'application/json',
                                                                          'X-Rapidci-Master-Key': self.flask_app.rapid_config.api_key,
                                                                          Version.HEADER: Version.get_version()})
        raise Exception('Not Allowed')

    def store_client(self, remote_addr, definition):
        clients = self._get_clients()
        clients[remote_addr] = definition
        self._save_clients(clients)

    def _save_clients(self, clients):
        StoreService.save_clients(clients, self.flask_app)

    def _get_clients(self):
        return StoreService.get_clients(self.flask_app)
