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
from mock.mock import MagicMock

from rapid.workflow.events.handlers.remote_notification_handler import RemoteNotificationHandler, RemoteNotification
from tests.framework.unit_test import UnitTest


class TestRemoteNotificationHandler(UnitTest):
    def test_prepare_payload(self):
        handler = RemoteNotificationHandler()

        self.assertEqual({'testing': 'trial'}, handler.prepare_payload({'payload': {
            'testing': '{testing}'
        }}, MagicMock(), MagicMock(), {'testing': 'trial'}))

    def test_remote_notification_init(self):
        notification = RemoteNotification({'headers': {'1': 2}, 'url': 'http:/testing', 'payload': 'nope', 'verify': False})

        self.assertEqual({'1': 2}, notification.headers)
        self.assertEqual('http:/testing', notification.url)
        self.assertEqual('nope', notification.payload)
        self.assertEqual(False, notification.verify)

    def test_multiple_key_expansion_not_at_beginning(self):
        handler = RemoteNotificationHandler()
        config = handler.prepare(
                                  {"url": "",
                                   "verify": False,
                                   "headers": {},
                                   "payload": {"message": "This is a test {actionInstance.id}. Pipeline {pipelineInstance.id}"},
                                   "conditional": "actionInstance.action.id == 1 and actionInstance.status_id > 4 and {release_id} != ''"}, TrialMock(1), TrialMock(2))
        self.assertEqual('This is a test {2}. Pipeline {1}', config['payload']['message'])


class TrialMock(object):
    def __init__(self, id):
        self.id = id

    def get_parameters_dict(self):
        return {"id": self.id}
