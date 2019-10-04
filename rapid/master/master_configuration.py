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
import uuid
from ..lib.configuration import Configuration

# pylint: disable=too-many-instance-attributes,too-few-public-methods


class MasterConfiguration(Configuration):
    def __init__(self, file_name=None):
        self.port = None
        self.queue_time = None
        self.db_connect_string = None
        self.data_type = None
        self.queue_manager = None
        self.queue_consider_late_time = None
        self.register_api_key = None
        self.api_key = None
        self.github_user = None
        self.github_webhooks_key = None
        self.github_default_parameters = None
        self.install_uri = None
        self.install_options = None
        self.verify_certs = None
        self.custom_reports_dir = None
        self.static_file_directory = None
        self.basic_auth_user = None
        self.basic_auth_pass = None
        self.basic_auth = None
        self.ecs_config_file = None

        super(MasterConfiguration, self).__init__(file_name)

    def set_basic_auth(self, basic_auth):
        if basic_auth:
            (self.basic_auth_user, self.basic_auth_pass) = basic_auth.split(':')

    def _set_values(self, parser):
        super(MasterConfiguration, self)._set_values(parser)
        self.set_basic_auth(self.basic_auth)

    @property
    def section_mapping(self):
        return {
            'master': {
                'port': [8080, int],
                'queue_time': [6, int],
                'db_connect_string': ['sqlite:///data.db'],
                'data_type': ['inmemory'],
                'queue_manager': [True, bool],
                'queue_consider_late_time': [10, float],
                'register_api_key': [str(uuid.uuid3(uuid.NAMESPACE_OID, 'RegisterApiKey!')).replace('-', '')],
                'api_key': [str(uuid.uuid3(uuid.NAMESPACE_OID, 'MasterApiKey!')).replace('-', '')],
                'github_user': [None],
                'github_pass': [None],
                'github_webhooks_key': [None],
                'github_default_parameters': [None],
                'custom_reports_dir': [None],
                'static_file_directory': [None],
                'basic_auth': [None]
            },
            'general': {
                'install_uri': ['https://pypi.python.org/pypi/'],
                'install_options': [''],
                'verify_certs': [True, bool],
                'log_file': [None]
            },
            'ecs': {
                'ecs_config_file': [None]
            }
        }
