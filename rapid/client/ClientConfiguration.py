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

from requests.auth import HTTPBasicAuth

from ..lib.Configuration import Configuration
import uuid


class ClientConfiguration(Configuration):

    def __init__(self, file_name=None):
        self.port = None
        self.workspace = None
        self.master_uri = None
        self.registration_rate = None
        self.executor_count = None
        self.grains = None
        self.grain_restrict = None
        self.quarantine_directory = None
        self.register_api_key = None
        self.api_key = None
        self.install_uri = None
        self.install_options = None
        self.get_files_basic_auth = None
        self.use_ssl = None
        self.verify_certs = None

        super(ClientConfiguration, self).__init__(file_name)
        self.executors = []

    def _set_values(self, parser):
        self._set_parser_value(parser, 'client', 'port', 8081, int)
        self._set_parser_value(parser, 'client', 'workspace', '/tmp/rapidci/workspace')
        self._set_parser_value(parser, 'client', 'master_uri', 'http://rapidci.local')
        self._set_parser_value(parser, 'client', 'registration_rate', 180, int)
        self._set_parser_value(parser, 'client', 'executor_count', 2, int)
        self._set_parser_value(parser, 'client', 'grains', None)
        self._set_parser_value(parser, 'client', 'grain_restrict', False, bool)
        self._set_parser_value(parser, 'client', 'quarantine_directory', '/tmp/rapidci/quarantine')
        self._set_parser_value(parser, 'client', 'register_api_key', None)
        self._set_parser_value(parser, 'client', 'api_key', str(uuid.uuid3(uuid.NAMESPACE_OID, 'ClientApiKey!')).replace('-', ''))
        self._set_parser_value(parser, 'client', 'install_uri', 'https://pypi.python.org/pypi/')
        self._set_parser_value(parser, 'client', 'install_options', '')
        self._set_parser_value(parser, 'client', 'get_files_basic_auth', None, list, ':')
        self._set_parser_value(parser, 'general', 'use_ssl', False, bool)
        self._set_parser_value(parser, 'general', 'verify_certs', True, bool)

        if self.get_files_basic_auth:
            try:
                self.get_files_basic_auth = HTTPBasicAuth(self.get_files_basic_auth[0], self.get_files_basic_auth[1])
            except:
                pass

