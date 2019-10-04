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
import uuid
import tempfile

from requests.auth import HTTPBasicAuth

from ..lib.configuration import Configuration

# pylint: disable=too-many-instance-attributes, too-few-public-methods


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
        self.log_file = None

        self.is_single_use = False

        super(ClientConfiguration, self).__init__(file_name)
        self.executors = []

    @property
    def section_mapping(self):
        return {
            'client': {
                'port': [8081, int],
                'workspace': [os.path.join(tempfile.gettempdir(), 'rapid', 'workspace')],
                'master_uri': ['http://rapidci.local'],
                'registration_rate': [180, int],
                'executor_count': [2, int],
                'grains': [None],
                'grain_restrict': [False, bool],
                'quarantine_directory': [os.path.join(tempfile.gettempdir(), 'rapid', 'quarantine')],
                'register_api_key': [None],
                'api_key': [str(uuid.uuid3(uuid.NAMESPACE_OID, 'ClientApiKey!')).replace('-', '')],
                'install_uri': ['https://pypi.python.org/pypi/'],
                'install_options': [''],
                'get_files_basic_auth': [None, list, ':']
            },
            'general': {
                'use_ssl': [False, bool],
                'verify_certs': [True, bool],
                'log_file': [None]
            }
        }

    def _set_values(self, parser):
        super(ClientConfiguration, self)._set_values(parser)

        if self.get_files_basic_auth:
            try:
                self.get_files_basic_auth = HTTPBasicAuth(self.get_files_basic_auth[0], self.get_files_basic_auth[1])
            except Exception:  # pylint: disable=broad-except
                pass

