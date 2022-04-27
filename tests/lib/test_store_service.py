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

from unittest.case import TestCase
from unittest.mock import Mock, patch

import jsonpickle
from nose.tools import eq_, ok_

from rapid.lib.store_service import StoreService


class TestStoreService(TestCase):

    def test_set_updating_no_uwsgi(self):
        config = Mock()
        StoreService.set_updating(config)

        eq_(True, StoreService.is_updating(config))

    @patch("rapid.lib.store_service.uwsgi")
    def test_set_updating_with_uwsgi(self, uwsgi):
        config = Mock()
        StoreService.set_updating(config)

        uwsgi.cache_update.assert_called_with("_rapidci_updating", jsonpickle.dumps(True))

    @patch("rapid.lib.store_service.uwsgi")
    def test_is_updating_no_uwsgi(self, uwsgi):
        config = Mock(rapid_config=Mock(_rapidci_updating=True))

        eq_(True, StoreService.is_updating(config))

    @patch("rapid.lib.store_service.uwsgi")
    def test_is_updating_with_uwsgi(self, uwsgi):
        config = Mock()
        uwsgi.cache_get.return_value = jsonpickle.dumps(True)

        eq_(True, StoreService.is_updating(config))

    def test_get_master_key_no_uwsgi(self):
        config = Mock(rapid_config=Mock(_rapidci_master_key="API_KEY"))
        eq_("API_KEY", StoreService.get_master_key(config))

    @patch("rapid.lib.store_service.uwsgi")
    def test_get_master_key_with_uwsgi(self, uwsgi):
        config = Mock()
        uwsgi.cache_get.return_value = jsonpickle.dumps("API_KEY")

        eq_("API_KEY", StoreService.get_master_key(config))

    def test_save_master_key_no_uwsgi(self):
        config = Mock(rapid_config=Mock(_rapidci_master_key=None))
        StoreService.save_master_key(config, "API_KEY")
        eq_("API_KEY", StoreService.get_master_key(config))

    @patch("rapid.lib.store_service.uwsgi")
    def test_save_master_key_with_uwsgi(self, uwsgi):
        config = Mock()
        StoreService.save_master_key(config, "API_KEY")

        uwsgi.cache_update.assert_called_with("_rapidci_master_key", jsonpickle.dumps("API_KEY"))

    @patch("rapid.lib.store_service.os")
    def test_check_pidfile(self, os):
        os.listdir.return_value = ['rapid-111-1111']
        ok_(StoreService.check_for_pidfile(111), "Pidfile should be found")

    @patch("rapid.lib.store_service.os")
    def test_check_pidfile(self, os):
        os.listdir.return_value = ['rapid-11-1111']
        ok_(not StoreService.check_for_pidfile(111), "Pidfile should not be found")

    def test_inmemory_store_for_service(self):
        StoreService.set_calculating_workflow(12345)
        StoreService.set_completing(12345)
        StoreService.set_updating(12345)
        self.assertTrue(StoreService.is_updating(12345))
        self.assertTrue(StoreService.is_calculating_workflow(12345))
        self.assertTrue(StoreService.is_completing(12345))
        StoreService.clear_calculating_workflow(12345)
        StoreService.clear_completing(12345)
        self.assertFalse(StoreService.is_calculating_workflow(12345))
        self.assertFalse(StoreService.is_completing(12345))

    @patch('rapid.lib.store_service.os')
    def test_check_for_pid_file(self, os):
        os.listdir.return_value = ['rapid-12345.txt']
        self.assertEqual('rapid-12345.txt', StoreService.check_for_pidfile('12345'))

    @patch('rapid.lib.store_service.tempfile')
    @patch('rapid.lib.store_service.os')
    def test_get_executors_with_nothing_to_see_returns_empty(self, os, tempfile):
        os.listdir.return_value = []
        self.assertEqual([], StoreService.get_executors())

    @patch('rapid.lib.store_service.tempfile')
    @patch('rapid.lib.store_service.psutil')
    @patch('rapid.lib.store_service.os')
    def test_get_executors_returns_what_is_running(self, os, psutil, tempfile):
        os.listdir.return_value = ['rapid-1-12']
        psutil.pids.return_value = [12]
        tempfile.gettempdir.return_value = '/tmp/boo'

        self.assertEqual([{'action_instance_id': '1', 'pid': '12'}], StoreService.get_executors())
        psutil.pids.assert_called_with()

    @patch('rapid.lib.store_service.tempfile')
    @patch('rapid.lib.store_service.psutil')
    @patch('rapid.lib.store_service.os')
    def test_get_executors_filters_invalid_running_pids(self, os, psutil, tempfile):
        psutil.pids.return_value = [12345]
        os.listdir.return_value = ['rapid-1-12']
        os.path.join.return_value = 'flibertygibet'
        tempfile.gettempdir.return_value = '/tmp/boo'

        os.kill.side_effect = OSError('foobar')

        self.assertEqual([], StoreService.get_executors())
        psutil.pids.assert_called_with()
        os.remove.assert_called_with('flibertygibet')
