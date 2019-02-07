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

from unittest.case import TestCase

from mock.mock import Mock, patch
from nose.tools.trivial import eq_

from rapid.client.communicator.client_communicator import ClientCommunicator
from rapid.master.master_configuration import MasterConfiguration


class TestClientCommunicator(TestCase):

    def test_init(self):
        mock_app = Mock()
        client_communicator = ClientCommunicator("bogus", "/tmp/trial", mock_app)

        eq_("bogus", client_communicator.server_uri)
        eq_("/tmp/trial", client_communicator.quarantine_directory)
        eq_(mock_app, client_communicator.flask_app)

    @patch("rapid.client.communicator.client_communicator.socket")
    def test_register_post_data(self, socket):
        config = MasterConfiguration()
        config.grain_restrict = False
        config.grains = "one;two"

        socket.gethostname.return_value = "bogus"

        test = {"grains": "one;two", "grain_restrict": False, "hostname": 'bogus'}
        eq_(test, json.loads(ClientCommunicator._get_register_post_data(config)))

    @patch("rapid.client.communicator.client_communicator.time")
    def test_get_register_headers(self, time):
        time.time.return_value = 1
        config = MasterConfiguration()
        config.register_api_key = 'Testing!@$%^'

        test = {'Content-Type': 'application/json',
                'X-RAPIDCI-PORT': config.port,
                'X-RAPIDCI-REGISTER-KEY': config.register_api_key,
                'X-RAPIDCI-TIME': 1000,
                'X-RAPIDCI-CLIENT-KEY': config.api_key}
        eq_(test, ClientCommunicator._get_register_headers(config))
