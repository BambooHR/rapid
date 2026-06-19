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
from unittest import TestCase

from flask import Response
from mock import MagicMock, Mock, patch

from rapid.lib.exceptions import HttpException
from rapid.master.controllers.api.utility_controller import UtilityRouter


def _make_router():
    app = Mock()
    app.rapid_config.register_api_key = 'reg-key'
    app.rapid_config.api_key = 'master-key'
    return UtilityRouter(flask_app=app)


def _make_request(content_type='application/json', register_key='reg-key',
                  client_key='client-key', port='8080', body=None):
    req = Mock()
    req.remote_addr = '10.0.0.1'
    req.headers = {
        'Content-Type': content_type,
        'X-Rapidci-Register-Key': register_key,
        'X-Rapidci-Client-Key': client_key,
        'X-Rapidci-port': port,
    }
    req.json = body or {'hostname': 'host', 'grains': ''}
    return req


class TestUtilityRouter(TestCase):
    def setUp(self):
        self.router = _make_router()

    def test_json_response_passes_through_existing_response_object_unchanged(self):
        from rapid.lib import json_response
        expected = Response('{}', content_type='application/json', headers={'X-Custom': 'val'})

        @json_response()
        def view():
            return expected

        self.assertIs(expected, view())

    def test_json_response_encodes_dict_return_value_to_json(self):
        from rapid.lib import json_response

        @json_response()
        def view():
            return {'key': 'value'}

        self.assertIn(b'"key"', view().data)

    def test_register_request_raises_unauthorized_when_content_type_is_not_json(self):
        with self.assertRaises(HttpException):
            self.router.register_request(_make_request(content_type='text/plain'))

    def test_register_request_raises_unauthorized_when_register_key_is_invalid(self):
        with self.assertRaises(HttpException):
            self.router.register_request(_make_request(register_key='bad-key'))

    def test_register_request_raises_unauthorized_when_client_api_key_is_missing(self):
        req = _make_request()
        req.headers = {k: v for k, v in req.headers.items() if k != 'X-Rapidci-Client-Key'}
        with self.assertRaises(HttpException):
            self.router.register_request(req)

    @patch('rapid.master.controllers.api.utility_controller.jsonpickle.encode', return_value='{}')
    @patch.object(UtilityRouter, 'store_client')
    @patch('rapid.master.controllers.api.utility_controller.Client')
    def test_register_request_returns_response_with_master_key_header_on_valid_request(self, mock_client, mock_store, _):
        mock_client.return_value = MagicMock()
        response = self.router.register_request(_make_request())
        self.assertIsInstance(response, Response)
        self.assertEqual('master-key', response.headers.get('X-Rapidci-Master-Key'))
