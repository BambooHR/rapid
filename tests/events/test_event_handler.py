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
from mock.mock import MagicMock, patch

from rapid.lib.constants import EventTypes
from rapid.workflow.events.event_dal import EventDal
from rapid.workflow.events.event_handler import EventHandlerFactory
from rapid.workflow.events.handlers.remote_notification_handler import RemoteNotificationHandler
from tests.framework.unit_test import UnitTest


class TestEventHandler(UnitTest):
    def test_factory_get_event_handler_valid_type(self):
        self.assertEqual(RemoteNotificationHandler.get_event_type(), EventHandlerFactory.get_event_handler(EventTypes.RemoteNotification.value).get_event_type())

    def test_factory_get_invalid_handler_returns_none(self):
        self.assertEqual(None, EventHandlerFactory.get_event_handler(None))

    def test_prepare_conditional(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance.get_parameters_dict.return_value = {'__testing__': 12}
        self.assertEqual('12 == 12', handler._prepare_conditional('{__testing__} == 12', mock_pipeline_instance, MagicMock()))

    def test_get_attribute_trait(self):
        handler = RemoteNotificationHandler()
        self.assertEqual(2, handler._get_attribute_trait(MagicMock(testing=MagicMock(trial=2)), 'testing.trial'))

    def test_evaluate_condition(self):
        handler = RemoteNotificationHandler()
        self.assertEqual('2 == 2 and 1 == 1 and 4 == 4',
            handler._prepare_conditional('pipelineInstance.status_id == 2 and actionInstance.action.id == 1 and actionInstance.status_id == 4',
                                         MagicMock(status_id=2),
                                         MagicMock(action=MagicMock(id=1),
                                                   status_id=4)))

    def test_passes_conditional_passes(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance.get_parameters_dict.return_value = {}

        self.assertTrue(handler.passes_conditional(mock_pipeline_instance,
                                       MagicMock(action=MagicMock(id=1),
                                                 status_id=4),
                                       'pipelineInstance.status_id == 2 and actionInstance.action.id == 1 and actionInstance.status_id == 4'))

    def test_passes_conditional_fails(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance.get_parameters_dict.return_value = {}

        self.assertTrue(not handler.passes_conditional(mock_pipeline_instance,
                                           MagicMock(action=MagicMock(id=1),
                                                     status_id=4),
                                           'pipelineInstance.status_id == 1 and actionInstance.action.id == 1 and actionInstance.status_id == 4'))

    def test_passes_conditional_complex_passes(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance.get_parameters_dict.return_value = {'__testing__': 2, '__trial__': 'True'}

        self.assertTrue(handler.passes_conditional(mock_pipeline_instance,
                                       MagicMock(),
                                       'pipelineInstance.status_id == 2 and {__testing__} == 2 and {__trial__}'))

    def test_passes_conditional_complex_fails(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance.get_parameters_dict.return_value = {'__testing__': 2, '__trial__': 'True'}

        self.assertTrue(not handler.passes_conditional(mock_pipeline_instance,
                                       MagicMock(),
                                       'pipelineInstance.status_id == 2 && {__testing__} == 1 && {__trial__}'))

    def test_passes_conditional_complex_or_passes(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance.get_parameters_dict.return_value = {'__testing__': 2, '__trial__': 'True'}

        self.assertTrue(not handler.passes_conditional(mock_pipeline_instance,
                                           MagicMock(),
                                           '(pipelineInstance.status_id == 2 && {__testing__} == 1) || {__trial__}'))

    def test_translate_string_for_key_string(self):
        handler = RemoteNotificationHandler()
        self.assertEqual('2 == 2', handler._translate_string_for_key_string('pipelineInstance', MagicMock(status_id=2), 'pipelineInstance.status_id == 2'))

    def test_translate_string_for_key_not_found_key_string_returns_original(self):
        handler = RemoteNotificationHandler()
        self.assertEqual('pipelineInstance.status_id == "testing"', handler._translate_string_for_key_string('pipelineIn', MagicMock(status_id=2), 'pipelineInstance.status_id == "testing"'))

    @patch('rapid.workflow.events.handlers.remote_notification_handler.RemoteNotificationHandler._translate_string_for_key_string')
    def test_translate_string_for_pipeline_instance_contract(self, key_string):
        handler = RemoteNotificationHandler()
        magicMock = MagicMock()
        handler._translate_string_for_pipeline_instance(magicMock, '')
        self.assertEqual(1, key_string.call_count)
        key_string.assert_called_with('pipelineInstance', magicMock, '')

    @patch('rapid.workflow.events.handlers.remote_notification_handler.RemoteNotificationHandler._translate_string_for_key_string')
    def test_translate_string_for_action_instance_contract(self, key_string):
        handler = RemoteNotificationHandler()
        magicMock = MagicMock()
        handler._translate_string_for_action_instance(magicMock, '')
        self.assertEqual(1, key_string.call_count)
        key_string.assert_called_with('actionInstance', magicMock, '')

    @patch('rapid.workflow.events.event_dal.EventHandlerFactory')
    def test_trigger_possible_event_utilizes_object_structure(self, handler_factory):
        mock_handler = MagicMock()
        handler_factory.get_event_handler.return_value = mock_handler
        mock_dal = MagicMock()
        mock_dal.get_pipeline_events_by_pipeline_id.return_value = [MagicMock(event_type_id=1)]

        handler = EventDal(mock_dal)
        handler.trigger_possible_event(MagicMock(), None, None)

        self.assertEqual(1, handler_factory.get_event_handler.call_count)
        self.assertEqual(1, mock_handler.handle_event.call_count)

    def test_get_event_handler_returns_properly(self):
        handler = EventHandlerFactory.get_event_handler(EventTypes.RemoteNotification.value)
        self.assertTrue(isinstance(handler, RemoteNotificationHandler))

    def test_get_event_handler_by_type_id(self):
        handler = EventHandlerFactory.get_event_handler(1)
        self.assertTrue(isinstance(handler, RemoteNotificationHandler))
