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
from tests.framework.unit_test import UnitTest

try:
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import ConfigParser as SafeConfigParser

from rapid.master.master_configuration import MasterConfiguration


class TestMasterConfiguration(UnitTest):

    def test_default_port(self):
        config = MasterConfiguration()
        config._set_values(None)

        self.assertEqual(8080, config.port, "Default Port not set.")

    def test_default_queue_time(self):
        config = MasterConfiguration()
        config._set_values(None)

        self.assertEqual(6, config.queue_time, "Default Queue Time not set.")

    def test_default_db_connect_string(self):
        config = MasterConfiguration()
        config._set_values(None)

        self.assertEqual('sqlite:///data.db', config.db_connect_string, "Default DB Connect String not set.")

    def test_default_data_type(self):
        config = MasterConfiguration()
        config._set_values(None)

        self.assertEqual('inmemory', config.data_type, "Default Data Type not set.")

    def test_config_override(self):
        config = MasterConfiguration()
        parser = SafeConfigParser({'master': {'port': '8881'}})
        parser.add_section('master')
        parser.set('master', 'port', '8881')
        config._set_values(parser)

        self.assertEqual(8881, config.port, "Config override did not work right. [8881 != {}]".format(config.port))

    def test_config_get_section(self):
        config = MasterConfiguration()
        self.assertEqual('master', config.get_section('api_key'))

    def test_custom_reports_dir(self):
        config = MasterConfiguration()
        parser = SafeConfigParser({'master': {'custom_reports_dir': "/tmp/trial"}})
        parser.add_section('master')
        parser.set('master', 'custom_reports_dir', "/tmp/trial")

        config._set_values(parser)
        self.assertEqual("/tmp/trial", config.custom_reports_dir)

    def test_git_default_parameters(self):
        config = MasterConfiguration()
        parser = SafeConfigParser({'master': {'github_default_parameters': "repository:repository.clone_url\nssh_url:respository.ssh_url"}})
        parser.add_section('master')
        parser.set('master', 'github_default_parameters', "repository:repository.clone_url\nssh_url:respository.ssh_url")

        config._set_values(parser)
        self.assertEqual("repository:repository.clone_url\nssh_url:respository.ssh_url", config.github_default_parameters)

    def test_basic_auth_consumption_and_setting(self):
        config = MasterConfiguration()
        parser = SafeConfigParser({'master': {'basic_auth': 'foo:bar'}})
        parser.add_section('master')
        parser.set('master', 'basic_auth', 'foo:bar')

        config._set_values(parser)
        self.assertEqual('foo', config.basic_auth_user)
        self.assertEqual('bar', config.basic_auth_pass)

    def test_ecs_config_file_parsing(self):
        config = MasterConfiguration()
        parser = SafeConfigParser()
        parser.add_section('ecs')
        parser.set('ecs', 'ecs_config_file', 'foobar')

        config._set_values(parser)
        self.assertEqual('foobar', config.ecs_config_file)


