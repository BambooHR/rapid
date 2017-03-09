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

from ..lib.Configuration import Configuration
import uuid


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

        super(MasterConfiguration, self).__init__(file_name)

    def _set_values(self, parser):
        self._set_parser_value(parser, 'master', 'port', 8080, int)
        self._set_parser_value(parser, 'master', 'queue_time', 6, int)
        self._set_parser_value(parser, 'master', 'db_connect_string', 'sqlite:///data.db')
        self._set_parser_value(parser, 'master', 'data_type', 'inmemory')
        self._set_parser_value(parser, 'master', 'queue_manager', True, bool)
        self._set_parser_value(parser, 'master', 'queue_consider_late_time', 10, float)
        self._set_parser_value(parser, 'master', 'register_api_key', None)
        self._set_parser_value(parser, 'master', 'api_key', str(uuid.uuid3(uuid.NAMESPACE_OID, 'MasterApiKey!')).replace('-', ''))
        self._set_parser_value(parser, 'master', 'github_user', None)
        self._set_parser_value(parser, 'master', 'github_pass', None)
        self._set_parser_value(parser, 'master', 'github_webhooks_key', None)
        self._set_parser_value(parser, 'master', 'github_default_parameters', None)
        self._set_parser_value(parser, 'master', 'custom_reports_dir', None)

        self._set_parser_value(parser, 'general', 'install_uri', None)
        self._set_parser_value(parser, 'general', 'install_options', '')
        self._set_parser_value(parser, 'general', 'verify_certs', True, bool)

