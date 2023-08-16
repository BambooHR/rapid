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
from rapid.client.client_configuration import ClientConfiguration
from tests.framework.unit_test import UnitTest

try:
    import simplejson as json
except:
    import json

from mock.mock import Mock, patch

from rapid.client.communicator.client_communicator import ClientCommunicator
from rapid.master.master_configuration import MasterConfiguration


class TestClientCommunicator(UnitTest):

    def test_init(self):
        mock_app = Mock()
        client_communicator = ClientCommunicator("bogus", "/tmp/trial", mock_app)

        self.assertEqual("bogus", client_communicator.server_uri)
        self.assertEqual("/tmp/trial", client_communicator.quarantine_directory)
        self.assertEqual(mock_app, client_communicator.flask_app)

    @patch("rapid.client.communicator.client_communicator.socket")
    def test_register_post_data(self, socket):
        config = MasterConfiguration()
        config.grain_restrict = False
        config.grains = "one;two"

        socket.gethostname.return_value = "bogus"

        test = {"grains": "one;two", "grain_restrict": False, "hostname": 'bogus'}
        self.assertEqual(test, json.loads(ClientCommunicator._get_register_post_data(config)))

    @patch("rapid.client.communicator.client_communicator.time")
    def test_get_register_headers(self, time):
        time.time.return_value = 1
        config = MasterConfiguration()
        config.register_api_key = 'Testing!@$%^'

        # per requests > 2.11.0 - All header values must be strings
        test = {'Content-Type': 'application/json',
                'X-RAPIDCI-PORT': str(config.port),
                'X-RAPIDCI-REGISTER-KEY': config.register_api_key,
                'X-RAPIDCI-TIME': '1000',
                'X-RAPIDCI-CLIENT-KEY': config.api_key}
        self.assertEqual(test, ClientCommunicator._get_register_headers(config))

    @patch('rapid.client.communicator.client_communicator.StoreService')
    @patch('rapid.client.communicator.client_communicator.requests')
    def test_default_send_includes_the_master_api_key(self, requests, store_service):
        mock_app = Mock(rapid_config=Mock(verify_certs=False))
        store_service.get_master_key.return_value='bogus_key'
        communicator = ClientCommunicator(None, flask_app=mock_app)
        requests.put.return_value = Mock(status_code=200)
        communicator._default_send('bogus', None)

        store_service.get_master_key.assert_called_with(mock_app)
        requests.put.assert_called_with('bogus', data=None, json=None, headers={'X-Rapidci-Api-Key': 'bogus_key'}, verify=False)

    @patch('rapid.client.communicator.client_communicator.StoreService')
    @patch('rapid.client.communicator.client_communicator.requests')
    @patch('rapid.client.communicator.client_communicator.ClientCommunicator._string_header_values')
    def test_default_send_stringifies_headers(self, header_values, requests, store_service):
        communicator = ClientCommunicator(None, flask_app=Mock())
        requests.put.return_value = Mock(status_code=200)
        communicator._default_send('bogus', None)

        header_values.assert_called_with(None)

    @patch('rapid.client.communicator.client_communicator.StoreService')
    @patch('rapid.client.communicator.client_communicator.requests')
    def test_default_send_defaults_to_put(self, requests, store_service):
        communicator = ClientCommunicator(None, flask_app=Mock())
        requests.put.return_value = Mock(status_code=200)
        communicator._default_send('bogus', None)

        requests.put.assert_called()

    @patch('rapid.client.communicator.client_communicator.StoreService')
    @patch('rapid.client.communicator.client_communicator.requests')
    def test_default_send_supports_post(self, requests, store_service):
        communicator = ClientCommunicator(None, flask_app=Mock())
        requests.post.return_value = Mock(status_code=200)
        communicator._default_send('bogus', None, 'post')

        requests.post.assert_called()

    @patch('rapid.client.communicator.client_communicator.StoreService')
    @patch('rapid.client.communicator.client_communicator.requests')
    def test_default_send_throws_exception(self, requests, store_service):
        communicator = ClientCommunicator(None, flask_app=Mock())
        requests.put.return_value = Mock(status_code=404)
        with self.assertRaises(Exception) as exception:
            communicator._default_send('bogus', None)

        self.assertEqual('Status Code Failure: 404', str(exception.exception))

    @patch('rapid.client.communicator.client_communicator.OSUtil')
    def test_get_real_file_name_empty_override_uses_os_path(self, patch_os):
        patch_os.path_join.return_value = '/testing/this/thing'
        communicator = ClientCommunicator(None)
        self.assertEqual('/testing/this/thing', communicator._get_real_file_name('foo', 'bar'))

    @patch('rapid.lib.utils.os.getenv')
    def test_get_real_file_name_not_empty_override(self, patch_env):
        patch_env.return_value = 'foobie_bubcus'
        communicator = ClientCommunicator(None)
        self.assertEqual('foofoobie_bubcusbar', communicator._get_real_file_name('foo', 'bar'))

    def test_trial(self):
        config = ClientConfiguration('/Users/mbright/code/cihub/vagrantconf/configs/rapid.cfg')
        client_communicator = ClientCommunicator(None)
        print(client_communicator._get_real_file_name('/mnt/d/rapid/workspace', '/ci/build.sh'))
