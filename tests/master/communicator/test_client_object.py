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
    import simplejson as json
except:
    import json

from mock.mock import patch

from rapid.lib import version
from rapid.lib.work_request import WorkRequest
from rapid.master.communicator.client import Client


class TestClientObject(UnitTest):

    def test_can_handle(self):
        client = Client('127.0.0.1', 9000, None, None)

        self.assertTrue(client.can_handle('something'))

    def test_can_handle_label(self):
        client = Client('127.0.0.1', 9000, 'something', None)

        self.assertTrue(True, client.can_handle('something'))

    def test_can_handle_not_label(self):
        client = Client('127.0.0.1', 9000, 'only', None)

        self.assertTrue(not client.can_handle('something'))

    def test_get_availability_url(self):
        client = Client('127.0.0.1', 9000, None, None)

        self.assertEqual("http://127.0.0.1:9000/work/request", client.get_availability_uri())

    def test_can_handle_complex_grain(self):
        client = Client('127.0.0.1', 9000, 'one;two;three', None)

        self.assertTrue(client.can_handle('one;two'))

    def test_can_handle_complex_grain_restricted(self):
        client = Client('127.0.0.1', 9000, 'one;two;three', True)

        self.assertTrue(not client.can_handle('one;two'))

    def test_can_handle_complex_grain_restricted_approve(self):
        client = Client('127.0.0.1', 9000, 'one;two;three', True)

        self.assertTrue(client.can_handle('two;three;one'))

    def test_can_handle_not_restricted_complex(self):
        client = Client('127.0.0.1', 9000, 'one;two;three', False)

        self.assertTrue(client.can_handle(None))

    def test_can_handle_not_restricted_empty_string(self):
        client = Client('127.0.0.1', 9000, 'one;two;three', False)

        self.assertTrue(not client.can_handle(''))

    def test_can_handle_while_asleep(self):
        client = Client('127.0.0.1', 9000, 'one;two;three', False)

        client.sleep = True
        self.assertTrue(not client.can_handle('one'))

    def test_can_handle_multiple_grain(self):
        client = Client('127.0.0.1', 9000, 'one;two;three', False)

        self.assertTrue(client.can_handle("one;two"))

    def test_get_state(self):
        client = Client('127.0.0.1', 9000, 'one;to;three', False, 'ApiKey', hostname='bogus', time_elapse=1000)

        self.assertEqual({'grain_restrict': False,
             'is_ssl': False,
             'sleep': False,
             'grains': ['one', 'to', 'three'],
             'api_key': 'ApiKey',
             'ip_address': '127.0.0.1',
             'port': 9000,
             'time_elapse': 1.5,
             'hostname': 'bogus'}, client.__getstate__())

    def test_get_headers(self):
        client = Client(None, None, None, None, 'trial', False)
        self.assertEqual({'X-Rapidci-Version': version.__version__, 'Content-Type': 'application/json', 'X-Rapidci-Api-Key': "trial"}, client.get_headers())

    def test_grain_restrict(self):
        client = Client(None, None, None, True)
        self.assertEqual(False, client.can_handle(""))

    def test_get_work_uri(self):
        client = Client("127.0.0.1", '8097', None, False)
        self.assertEqual("http://127.0.0.1:8097/work/execute", client.get_work_uri())

    def test_get_status_uri(self):
        client = Client("127.0.0.1", '8097', None, False)
        self.assertEqual("http://127.0.0.1:8097/status", client.get_status_uri())

    @patch("rapid.master.communicator.client.requests")
    def test_send_work(self, requests):
        client = Client(None, None, None, False)
        work_request = WorkRequest()

        client.send_work(work_request)
        self.assertEqual(1, requests.post.call_count)
        requests.post.assert_called_with(client.get_work_uri(), json=work_request.__dict__, headers=client.get_headers(), verify=True, timeout=4)
