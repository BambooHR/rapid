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
    from ConfigParser import SafeConfigParser
except ImportError:
    from configparser import ConfigParser as SafeConfigParser

from nose.tools import eq_
from unittest import TestCase
from rapid.master.master_configuration import MasterConfiguration


class TestMasterConfiguration(TestCase):

    def test_default_port(self):
        config = MasterConfiguration()
        config._set_values(None)

        eq_(8080, config.port, "Default Port not set.")

    def test_default_queue_time(self):
        config = MasterConfiguration()
        config._set_values(None)

        eq_(6, config.queue_time, "Default Queue Time not set.")

    def test_default_db_connect_string(self):
        config = MasterConfiguration()
        config._set_values(None)

        eq_('sqlite:///data.db', config.db_connect_string, "Default DB Connect String not set.")

    def test_default_data_type(self):
        config = MasterConfiguration()
        config._set_values(None)

        eq_('inmemory', config.data_type, "Default Data Type not set.")

    def test_config_override(self):
        config = MasterConfiguration()
        parser = SafeConfigParser({'master': {'port': '8881'}})
        parser.add_section('master')
        parser.set('master', 'port', '8881')
        config._set_values(parser)

        eq_(8881, config.port, "Config override did not work right. [8881 != {}]".format(config.port))
