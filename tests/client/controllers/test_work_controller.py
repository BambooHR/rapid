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
import datetime

import sys
from mock.mock import Mock, patch

from rapid.client.controllers.work_controller import WorkController
import rapid.lib
from rapid.lib import version
from tests.framework.unit_test import UnitTest


class TestWorkController(UnitTest):
    def test_register_rules(self):
        app = Mock()
        controller = WorkController()
        url_rules = [['/work/request', 'work_request', {'type_is': 'decorated_view',
                                                        'name': 'work_request',
                                                        'co_filename': '{}'.format(rapid.lib.__file__.replace('.pyc', '.py'))}],
                     ['/work/execute', 'work_execute', {'type_is': 'decorated_view',
                                                        'name': 'work_execute',
                                                        'co_filename': '{}'.format(rapid.lib.__file__.replace('.pyc', '.py'))}, {'methods': ['POST']}]]
        registered_rules = {}

        def set_url(*args, **kwargs):
            arguments = list(args)
            if sys.version.startswith('2'):  # TODO: Remove after moved to python3
                arguments[2] = {'type_is': args[2].func_code.co_name, 'name': args[2].func_name, 'co_filename': args[2].func_code.co_filename}
            else:
                arguments[2] = {'type_is': args[2].__code__.co_name,
                                'name': args[2].__wrapped__.__func__.__name__,
                                'co_filename': args[2].__code__.co_filename}
            if kwargs:
                arguments.append(kwargs)
            registered_rules[args[0]] = arguments

        app.add_url_rule = set_url

        controller.register_url_rules(app)
        for assertions in url_rules:
            self.assertEqual(registered_rules[assertions[0]], assertions)

    def test_app_is_tracked(self):
        app = Mock()
        controller = WorkController()

        controller.register_url_rules(app)
        self.assertEqual(app, controller.app)

    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_can_work_on_less_executors(self, store_service):
        controller = WorkController()
        controller.app = Mock()
        controller.app.rapid_config.executor_count = 1
        store_service.get_executors.return_value = []
        self.assertEqual(True, controller.can_work_on())

    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_can_work_on_equal_executors(self, store_service):
        controller = WorkController()
        controller.app = Mock()
        controller.app.rapid_config.executor_count = 1
        store_service.get_executors.return_value = [1]
        self.assertEqual(False, controller.can_work_on())

    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_can_work_on_more_executors(self, store_service):
        controller = WorkController()
        controller.app = Mock()
        controller.app.rapid_config.executor_count = 1
        store_service.get_executors.return_value = [1, 1]
        self.assertEqual(False, controller.can_work_on())

    @patch("rapid.lib.store_service.os")
    def test_can_work_on_with_work(self, os):
        controller = WorkController()
        controller.app = Mock()
        controller.app.rapid_config.executor_count = 1
        os.listdir.return_value = []

        self.assertEqual(True, controller.can_work_on(Mock(action_instance_id=1111)))

    @patch("rapid.lib.store_service.os")
    @patch("rapid.lib.store_service.psutil")
    def test_can_work_on_with_work_existing_action_instance(self, psutil, os):
        psutil.pids.return_value = [11111]
        controller = WorkController()
        controller.app = Mock()
        controller.app.rapid_config.executor_count = 1
        os.listdir.return_value = ['rapid-11-11111']

        self.assertEqual(False, controller.can_work_on(Mock(action_instance_id=11)))

    def test_check_version_empty_header(self):
        controller = WorkController()
        self.assertEqual(False, controller.check_version(Mock(headers={})), "Should return false when header is not present")

    def test_check_version_same_versions(self):
        controller = WorkController()
        self.assertEqual(True, controller.check_version(Mock(headers={version.Version.HEADER: version.__version__})))

    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_check_version_different_versions_is_updating(self, store_service):
        controller = WorkController()
        controller.app = Mock()
        store_service.is_updating.return_value = True
        self.assertEqual(False, controller.check_version(Mock(headers={version.Version.HEADER: "1"})))

    @patch("rapid.client.controllers.work_controller.threading")
    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_check_version_different_versions_is_not_updating(self, store_service, threading):
        controller = WorkController()
        controller.app = Mock()
        store_service.is_updating.return_value = False
        self.assertEqual(False, controller.check_version(Mock(headers={version.Version.HEADER: "1"})))
        self.assertEqual(1, threading.Thread.call_count)

    def test_get_version(self):
        controller = WorkController()
        self.assertEqual(version.Version.get_version(), controller.get_version())

    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_sleep_for_executors_zero_length(self, store_service):
        store_service.get_executors.return_value = []

        self.assertEqual([], WorkController._sleep_for_executors())
        self.assertEqual(1, store_service.get_executors.call_count)

    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_sleep_for_executors_one_length(self, store_service):
        self.count = [1, 2]

        def decrease(*args, **kwargs):
            self.count.pop(0)
            return self.count

        store_service.get_executors = decrease
        work_time = datetime.datetime.now()
        WorkController._sleep_for_executors(.001, 2)
        now_time = datetime.datetime.now()

        self.assertTrue(400000 > (now_time - work_time).microseconds)

    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_sleep_for_executors_time_out(self, store_service):
        self.count = [1, 2, 3, 4]

        def decrease(*args, **kwargs):
            self.count.pop(0)
            return self.count

        store_service.get_executors = decrease

        WorkController._sleep_for_executors(0, 2)

        self.assertEqual([3, 4], self.count)

    @patch("rapid.client.controllers.work_controller.UpgradeUtil")
    def test_start_upgrade_no_executors(self, upgrade_util):
        controller = WorkController()
        controller.app = Mock(rapid_config="testing")

        controller._start_upgrade("12345", [])

        upgrade_util.upgrade_version.assert_called_with("12345", "testing")

    @patch("rapid.client.controllers.work_controller.logger")
    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_start_upgrade_with_executors(self, store_service, mock_logger):
        controller = WorkController()
        mock_app = Mock()
        controller.app = mock_app

        controller._start_upgrade("12345", [1])

        store_service.set_updating.assert_called_with(mock_app, False)

    @patch("rapid.client.controllers.work_controller.logger")
    @patch("rapid.client.controllers.work_controller.UpgradeUtil")
    @patch("rapid.client.controllers.work_controller.StoreService")
    def test_perform_upgrade(self, store_service, upgrade_util, mock_logger):
        controller = WorkController()
        controller.app = Mock(rapid_config="testing")

        store_service.get_executors.return_value = []

        controller._perform_upgrade("12345")
        upgrade_util.upgrade_version.assert_called_with("12345", "testing")

    @patch("rapid.client.controllers.work_controller.StoreService")
    @patch("rapid.client.controllers.work_controller.os")
    @patch("rapid.client.controllers.work_controller.Response")
    def test_work_cancel_should_not_cancel_if_action_instance_not_found(self, response, mock_os, store_service):
        controller = WorkController()
        store_service.check_for_pidfile.return_value = None

        controller.work_cancel(12345)
        self.assertEqual(501, response.call_args_list[0][0][1])

    @patch("rapid.client.controllers.work_controller.StoreService")
    @patch("rapid.client.controllers.work_controller.psutil")
    @patch("rapid.client.controllers.work_controller.Response")
    def test_work_cancel_should_cancel_if_action_instance_found(self, response, mock_psutil, store_service):
        controller = WorkController()
        store_service.check_for_pidfile.return_value = 'testing-1-2-3'

        controller.work_cancel(12345)
        mock_psutil.Process.assert_called_with(3)
        mock_psutil.Process().kill.assert_called_with()

    @patch("rapid.client.controllers.work_controller.StoreService")
    @patch("rapid.client.controllers.work_controller.os")
    @patch("rapid.client.controllers.work_controller.Response")
    def test_work_cancel_should_not_cancel_if_pid_not_found(self, response, mock_os, store_service):
        controller = WorkController()
        store_service.check_for_pidfile.return_value = "testing-1-2-3"
        mock_os.kill.side_effect = Exception("Booo")

        controller.work_cancel(124545)
        self.assertEqual(501, response.call_args_list[0][0][1])
