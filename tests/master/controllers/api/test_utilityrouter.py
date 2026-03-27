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
from unittest.mock import MagicMock, patch

from tests.framework.unit_test import UnitTest
from rapid.lib.exceptions import HttpException, VcsNotFoundException
from rapid.master.controllers.api.utility_controller import UtilityRouter
from rapid.master.communicator.client import Client

try:
    import simplejson as json
except ImportError:
    import json


class TestUtilityRouter(UnitTest):

    def setUp(self):
        self.flask_app = MagicMock()
        self.flask_app.rapid_config.register_api_key = 'test-register-key'
        self.flask_app.rapid_config.api_key = 'test-api-key'
        self.flask_app.rapid_config.verify_certs = True
        self.flask_app.rapid_config.queue_consider_late_time = 300
        self.router = UtilityRouter(self.flask_app)


    @patch('rapid.master.controllers.api.utility_controller.StoreService')
    def test_show_clients_returns_encoded_clients(self, mock_store):
        test_client = Client('192.168.1.1', 8080, 'linux', False, 'test-key', False, 'test-host', 1.0)
        mock_clients = {'192.168.1.1': test_client}
        mock_store.get_clients.return_value = mock_clients
        
        response = self.router.show_clients()
        
        self.assertEqual('application/json', response.content_type)
        mock_store.get_clients.assert_called_once_with(self.flask_app)
        
        decoded_data = jsonpickle.decode(response.data)
        self.assertIn('192.168.1.1', decoded_data)
        self.assertEqual('192.168.1.1', decoded_data['192.168.1.1'].ip_address)
        self.assertEqual(8080, decoded_data['192.168.1.1'].port)

    @patch('rapid.master.controllers.api.utility_controller.StoreService')
    @patch('rapid.master.controllers.api.utility_controller.MasterCommunicator')
    def test_client_still_working_on_returns_status_when_client_exists(self, mock_comm, mock_store):
        mock_client = MagicMock()
        mock_clients = {'192.168.1.1': mock_client}
        mock_store.get_clients.return_value = mock_clients
        mock_comm.is_still_working_on.return_value = True
        
        response = self.router.client_still_working_on('192.168.1.1', 'action-123')
        
        self.assertEqual('application/json', response.content_type)
        result = json.loads(response.data)
        self.assertEqual({'status': True}, result)
        mock_comm.is_still_working_on.assert_called_once_with('action-123', mock_client, True)

    @patch('rapid.master.controllers.api.utility_controller.StoreService')
    def test_client_still_working_on_returns_no_client_found(self, mock_store):
        mock_store.get_clients.return_value = {}
        
        response = self.router.client_still_working_on('192.168.1.1', 'action-123')
        
        self.assertEqual('application/json', response.content_type)
        result = json.loads(response.data)
        self.assertEqual({"status": "No client found"}, result)

    @patch('rapid.master.controllers.api.utility_controller.StoreService')
    def test_client_still_working_on_handles_exception(self, mock_store):
        mock_store.get_clients.side_effect = Exception("Store error")
        
        response = self.router.client_still_working_on('192.168.1.1', 'action-123')
        
        self.assertEqual('application/json', response.content_type)
        result = json.loads(response.data)
        self.assertEqual({"status": "No client found"}, result)

    @patch('rapid.master.controllers.api.utility_controller.ActionDal')
    def test_client_verify_working_calls_action_dal(self, mock_dal_class):
        mock_dal = MagicMock()
        mock_dal_class.return_value = mock_dal
        mock_dal.get_verify_working.return_value = {'working': True}
        
        response = self.router.client_verify_working()
        
        self.assertEqual('application/json', response.content_type)
        result = json.loads(response.data)
        self.assertEqual({'working': True}, result)
        mock_dal.get_verify_working.assert_called_once_with(300)

    @patch('rapid.master.controllers.api.utility_controller.StoreService')
    @patch('rapid.master.controllers.api.utility_controller.MasterCommunicator')
    def test_working_clients_groups_by_version(self, mock_comm, mock_store):
        mock_clients = [
            {'version': '1.0', 'name': 'client1'},
            {'version': '1.0', 'name': 'client2'},
            {'version': '2.0', 'name': 'client3'},
        ]
        mock_store.get_clients.return_value = MagicMock(values=MagicMock(return_value=[]))
        mock_comm.get_clients_working_on.return_value = mock_clients
        
        response = self.router.working_clients()
        
        self.assertEqual('application/json', response.content_type)
        data = json.loads(response.data)
        self.assertEqual(2, len(data['1.0']))
        self.assertEqual(1, len(data['2.0']))

    @patch('rapid.master.controllers.api.utility_controller.StoreService')
    @patch('rapid.master.controllers.api.utility_controller.MasterCommunicator')
    def test_working_clients_filters_none_values(self, mock_comm, mock_store):
        mock_clients = [
            {'version': '1.0', 'name': 'client1'},
            None,
            {'version': '1.0', 'name': 'client2'},
        ]
        mock_store.get_clients.return_value = MagicMock(values=MagicMock(return_value=[]))
        mock_comm.get_clients_working_on.return_value = mock_clients
        
        response = self.router.working_clients()
        
        data = json.loads(response.data)
        self.assertEqual(2, len(data['1.0']))

    @patch('rapid.master.controllers.api.utility_controller.Version')
    def test_register_request_creates_client_with_all_headers(self, mock_version):
        mock_version.get_version.return_value = '1.0.0'
        mock_version.HEADER = 'X-Rapidci-Version'
        
        mock_request = MagicMock()
        mock_request.headers = {
            'Content-Type': 'application/json',
            'X-Rapidci-Register-Key': 'test-register-key',
            'X-Rapidci-Client-Key': 'client-key',
            'X-Rapidci-port': '8080',
            'X-Rapidci-time': str(time.time() * 1000 - 500),
            'X-Is-Ssl': 'true'
        }
        mock_request.remote_addr = '192.168.1.1'
        mock_request.json = {
            'grains': 'linux;docker',
            'hostname': 'test-host',
            'grain_restrict': True
        }
        
        with patch.object(self.router, 'store_client'):
            response = self.router.register_request(mock_request)
        
        self.assertEqual('application/json', response.content_type)
        self.assertEqual('test-api-key', response.headers['X-Rapidci-Master-Key'])
        self.assertEqual('1.0.0', response.headers['X-Rapidci-Version'])

    def test_register_request_sets_ssl_true_for_port_443(self):
        mock_request = MagicMock()
        mock_request.headers = {
            'Content-Type': 'application/json',
            'X-Rapidci-Register-Key': 'test-register-key',
            'X-Rapidci-Client-Key': 'client-key',
            'X-Rapidci-time': 0,
            'X-Rapidci-port': '443'
        }
        mock_request.remote_addr = '192.168.1.1'
        mock_request.json = {}
        
        with patch.object(self.router, 'store_client'):
            response = self.router.register_request(mock_request)
        
        client = jsonpickle.decode(response.data)
        self.assertTrue(client.is_ssl)

    def test_register_request_raises_exception_when_no_api_key(self):
        mock_request = MagicMock()
        mock_request.headers = {
            'Content-Type': 'application/json',
            'X-Rapidci-Register-Key': 'test-register-key'
        }
        mock_request.remote_addr = '192.168.1.1'
        mock_request.json = {}
        
        with self.assertRaises(Exception) as context:
            self.router.register_request(mock_request)
        
        self.assertEqual("NO API KEY!", str(context.exception))

    def test_register_request_raises_exception_when_wrong_content_type(self):
        mock_request = MagicMock()
        mock_request.headers = {'Content-Type': 'text/plain'}
        
        with self.assertRaises(Exception) as context:
            self.router.register_request(mock_request)
        
        self.assertEqual('Not Allowed', str(context.exception))

    def test_register_request_raises_exception_when_wrong_register_key(self):
        mock_request = MagicMock()
        mock_request.headers = {
            'Content-Type': 'application/json',
            'X-Rapidci-Register-Key': 'wrong-key'
        }
        
        with self.assertRaises(Exception) as context:
            self.router.register_request(mock_request)
        
        self.assertEqual('Not Allowed', str(context.exception))
    @patch('rapid.master.controllers.api.utility_controller.StoreService')
    def test_store_client_saves_to_store_service(self, mock_store):
        mock_store.get_clients.return_value = {}
        mock_client = MagicMock()
        
        self.router.store_client('192.168.1.1', mock_client)
        
        mock_store.save_clients.assert_called_once()
        saved_clients = mock_store.save_clients.call_args[0][0]
        self.assertEqual(mock_client, saved_clients['192.168.1.1'])

    @patch('rapid.master.controllers.api.utility_controller.StoreService')
    def test_store_client_preserves_existing_clients(self, mock_store):
        existing_client = MagicMock()
        mock_store.get_clients.return_value = {'192.168.1.2': existing_client}
        new_client = MagicMock()
        
        self.router.store_client('192.168.1.1', new_client)
        
        saved_clients = mock_store.save_clients.call_args[0][0]
        self.assertEqual(2, len(saved_clients))
        self.assertEqual(existing_client, saved_clients['192.168.1.2'])
        self.assertEqual(new_client, saved_clients['192.168.1.1'])

    @patch('rapid.master.controllers.api.utility_controller.StoreService')
    def test_store_client_overwrites_existing_client_at_same_ip(self, mock_store):
        old_client = MagicMock()
        mock_store.get_clients.return_value = {'192.168.1.1': old_client}
        new_client = MagicMock()
        
        self.router.store_client('192.168.1.1', new_client)
        
        saved_clients = mock_store.save_clients.call_args[0][0]
        self.assertEqual(1, len(saved_clients))
        self.assertEqual(new_client, saved_clients['192.168.1.1'])
        self.assertNotEqual(old_client, saved_clients['192.168.1.1'])

    def test_register_request_calculates_time_elapse_correctly(self):
        current_time = time.time() * 1000
        elapsed_time = 1500
        
        mock_request = MagicMock()
        mock_request.headers = {
            'Content-Type': 'application/json',
            'X-Rapidci-Register-Key': 'test-register-key',
            'X-Rapidci-Client-Key': 'client-key',
            'X-Rapidci-time': str(current_time - elapsed_time)
        }
        mock_request.remote_addr = '192.168.1.1'
        mock_request.json = {}
        
        with patch.object(self.router, 'store_client'):
            with patch('rapid.master.controllers.api.utility_controller.time.time', return_value=current_time / 1000):
                response = self.router.register_request(mock_request)
        
        client = jsonpickle.decode(response.data)
        self.assertGreaterEqual(client.time_elapse, 1.5)

    def test_register_request_ensures_minimum_time_elapse(self):
        current_time = time.time() * 1000
        
        mock_request = MagicMock()
        mock_request.headers = {
            'Content-Type': 'application/json',
            'X-Rapidci-Register-Key': 'test-register-key',
            'X-Rapidci-Client-Key': 'client-key',
            'X-Rapidci-time': str(current_time + 100)
        }
        mock_request.remote_addr = '192.168.1.1'
        mock_request.json = {}
        
        with patch.object(self.router, 'store_client'):
            with patch('rapid.master.controllers.api.utility_controller.time.time', return_value=current_time / 1000):
                response = self.router.register_request(mock_request)
        
        client = jsonpickle.decode(response.data)
        self.assertGreaterEqual(client.time_elapse, 0.001)

    def test_register_request_ssl_header_false_value(self):
        mock_request = MagicMock()
        mock_request.headers = {
            'Content-Type': 'application/json',
            'X-Rapidci-Register-Key': 'test-register-key',
            'X-Rapidci-Client-Key': 'client-key',
            'X-Rapidci-time': 0,
            'X-Is-Ssl': 'false'
        }
        mock_request.remote_addr = '192.168.1.1'
        mock_request.json = {}
        
        with patch.object(self.router, 'store_client'):
            response = self.router.register_request(mock_request)
        
        client = jsonpickle.decode(response.data)
        self.assertFalse(client.is_ssl)

    def test_register_url_rules_registers_all_routes(self):
        self.router.register_url_rules()
        
        self.assertEqual(5, self.flask_app.add_url_rule.call_count)
        
        calls = self.flask_app.add_url_rule.call_args_list
        routes = {call[0][0]: call[0][1] for call in calls}
        
        self.assertIn('/clients/show', routes)
        self.assertIn('/client/register', routes)
        self.assertIn('/clients/working', routes)
        self.assertIn('/clients/<path:client_ip>/still_working/<path:action_instance_id>', routes)
        self.assertIn('/clients/verify_working', routes)

    def test_register_url_rules_registers_error_handlers(self):
        self.router.register_url_rules()
        
        self.assertEqual(2, self.flask_app.register_error_handler.call_count)
        
        calls = self.flask_app.register_error_handler.call_args_list
        error_types = [call[0][0] for call in calls]
        
        self.assertIn(HttpException, error_types)
        self.assertIn(VcsNotFoundException, error_types)
