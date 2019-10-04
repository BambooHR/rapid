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
import time
import pickle
import socket
import logging
import requests
from requests.exceptions import ConnectionError  # pylint: disable=redefined-builtin

from rapid.client.client_configuration import ClientConfiguration
from rapid.lib.constants import HeaderConstants

from rapid.lib.version import Version

try:
    import simplejson as json
except ImportError:
    import json

from rapid.lib.communicator import Communicator
from rapid.lib.store_service import StoreService

logger = logging.getLogger("rapid")

# pylint: disable=broad-except


class ClientCommunicator(Communicator):
    DOWNLOAD_URI = '/get_file/{}'
    REGISTRATION_URI = "/client/register"
    WORK_REQUEST_URI = "/api/action_instances/{}/work_request"

    def __init__(self, server_uri, quarantine_directory=None, flask_app=None, verify_certs=True, get_files_auth=None):
        """

        :param server_uri:
        :param quarantine_directory:
        :param flask_app:
        :param verify_certs:
        :type get_files_auth: :class:`requests.auth.HTTPBasicAuth`
        :return:
        """
        super(ClientCommunicator, self).__init__(server_uri, flask_app=flask_app)
        self.quarantine_directory = quarantine_directory
        self.verify_certs = verify_certs if not flask_app else flask_app.rapid_config.verify_certs
        self.get_files_auth = get_files_auth

    def get_work_request_by_action_instance_id(self, action_instance_id):
        return self._default_get(self.get_uri(self.WORK_REQUEST_URI.format(action_instance_id))).json()

    def get_file(self, directory, file_name, logger_in):
        """
        Download via requests, the file that is requested.
        :param logger_in:
        :param file_name:
        :return:
        """
        file_name = file_name.strip()
        uri = self.get_uri(self.DOWNLOAD_URI.format(file_name))
        try:
            local_file_name = self.get_downloaded_file_name(directory, file_name)
            return local_file_name
        except Exception:
            import traceback
            traceback.print_exc()
            logger_in.error("unable to download file: {}".format(uri))

    def send_parameters(self, pipeline_instance_id, parameters, logger_in):
        if parameters:
            try:
                self._default_send(self.api_uri("pipeline_instance/{}".format(pipeline_instance_id)), parameters)
            except Exception as exception:
                logger_in.error(exception)

    def send_statistics(self, action_instance_id, stats, logger_in):
        if stats:
            try:
                self._default_send(self.api_uri("action_instance/{}/stats".format(action_instance_id)), stats)
            except Exception as exception:
                logger_in.error(exception)

    def send_results(self, action_instance_id, results, logger_in):
        if results:
            try:
                self._default_send(self.api_uri("action_instance/{}/results".format(action_instance_id)), results)
            except Exception as exception:
                logger_in.error(exception)

    def send_test_analysis(self, pipeline_instance_id, analysis, logger_in):
        if analysis:
            try:
                self._default_send(self.api_uri("qa_tests/analysis"), None, 'post', {'X-Pipeline-Instance-Id': str(pipeline_instance_id)}, in_json=analysis)
            except Exception as exception:
                logger_in.error(exception)

    def send_done(self, action_instance_id, status, parameters, stats, results, logger_in, headers=None):
        data = {'status': status}

        if headers is None:
            headers = {"Content-Type": 'application/json'}
        else:
            headers['Content-Type'] = 'application/json'

        if parameters:
            data['parameters'] = parameters
        if stats:
            data['stats'] = stats
        if results:
            data['results'] = results

        try:
            self._default_send(self.api_uri("action_instances/{}/done".format(action_instance_id)), json.dumps(data), 'post',
                               headers)
        except Exception as exception:
            logger_in.error(exception)
            self._handle_quarantine_failure(exception, action_instance_id, data, logger_in)

    def _handle_quarantine_failure(self, exception, action_instance_id, data, logger_in):
        if self.quarantine_directory is not None \
                and ((isinstance(exception, ConnectionError) and ("Connection refused" in "{}".format(exception) or
                                                                  "Connection aborted" in "{}".format(exception))) or
                     'Status Code Failure:' in exception.message):
            try:
                os.makedirs(self.quarantine_directory)
            except Exception:
                pass

            message = "Master not available, storing for later: {}".format(action_instance_id)
            logger_in.error(message)

            with open('{}/{}'.format(self.quarantine_directory, action_instance_id), 'w') as tmp_file:
                tmp_file.writelines(pickle.dumps(data))
                tmp_file.flush()

    @staticmethod
    def _get_register_post_data(client_config):
        return json.dumps({"grains": client_config.grains,
                           "grain_restrict": client_config.grain_restrict,
                           "hostname": socket.gethostname()})

    @staticmethod
    def _get_register_headers(client_config):
        headers = {'Content-Type': 'application/json',
                   'X-RAPIDCI-PORT': str(client_config.port) if hasattr(client_config, 'port') else '',
                   'X-RAPIDCI-REGISTER-KEY': client_config.register_api_key if hasattr(client_config, 'register_api_key') else '',
                   'X-RAPIDCI-TIME': str(time.time() * 1000),
                   'X-RAPIDCI-CLIENT-KEY': client_config.api_key if hasattr(client_config, 'api_key') else ''}
        if hasattr(client_config, 'use_ssl') and client_config.use_ssl:
            headers['X-Is-Ssl'] = 'true'

        try:
            if client_config.is_single_use:
                headers[HeaderConstants.SINGLE_USE] = 'true'
        except (AttributeError, TypeError):
            pass

        return headers

    def register(self, client_config):
        # type: (ClientConfiguration) -> dict
        try:
            response = self._default_send(self.get_uri(self.REGISTRATION_URI),
                                          self._get_register_post_data(client_config),
                                          'post',
                                          self._get_register_headers(client_config))

            if response.status_code == 200 and 'X-Rapidci-Master-Key' in response.headers:
                StoreService.save_master_key(self.flask_app, response.headers['X-Rapidci-Master-Key'])
            return {'master_version': response.headers[Version.HEADER]}
        except Exception as exception:
            logger.error(exception)

    def _string_header_values(self, headers):
        _headers = {}
        try:
            for key, value in headers.items():
                _headers[key] = str(value) if value is not None else ''
        except (TypeError, AttributeError):
            pass
        return _headers

    def _default_get(self, uri):
        headers = {}
        master_key = StoreService.get_master_key(self.flask_app)
        headers = self._string_header_values(headers)

        if master_key is not None:
            headers['X-Rapidci-Api-Key'] = master_key

        return requests.get(uri, headers=headers)

    def _default_send(self, uri, data, in_type='put', headers=None, in_json=None):
        master_key = StoreService.get_master_key(self.flask_app)
        headers = self._string_header_values(headers)
        
        if master_key is not None:
            headers['X-Rapidci-Api-Key'] = master_key

        request = None
        if in_type == 'put':
            request = requests.put(uri, data=data, json=in_json, headers=headers, verify=self.verify_certs)
        elif in_type == 'post':
            request = requests.post(uri, data=data, json=in_json, headers=headers, verify=self.verify_certs)

        if request.status_code != 200:
            raise Exception("Status Code Failure: {}".format(request.status_code))
        return request

    def get_downloaded_file_name(self, directory, file_name):
        real_file_name = os.path.join(directory, file_name.split('/')[-1])  # required files must ALWAYS be with / not \
        try:
            os.makedirs(os.path.dirname(real_file_name))
        except Exception:
            pass

        with open(real_file_name, 'wb') as handle:
            response = None
            if self.get_files_auth is not None:
                response = requests.get(self.server_uri + "/get_file/{}".format(file_name), verify=self.verify_certs, auth=self.get_files_auth)
            else:
                response = requests.get(self.server_uri + "/get_file/{}".format(file_name), verify=self.verify_certs)

            if not response.ok:
                raise BaseException("File '{}' did not download".format(file_name))

            for block in response.iter_content(1024):
                handle.write(block)
        return real_file_name
