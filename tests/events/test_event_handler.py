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

from mock.mock import MagicMock
from nose.tools.trivial import ok_, eq_

from rapid.lib.Constants import EventTypes
from rapid.workflow.events.event_handler import EventHandlerFactory
from rapid.workflow.events.handlers.RemoteNotificationHandler import RemoteNotificationHandler


class TestEventHandler(TestCase):
    def test_factory_get_event_handler_valid_type(self):
        eq_(RemoteNotificationHandler.get_event_type(), EventHandlerFactory.get_event_handler(EventTypes.RemoteNotification).get_event_type())

    def test_factory_get_invalid_handler_returns_none(self):
        eq_(None, EventHandlerFactory.get_event_handler(None))

    def test_prepare_conditional(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock()
        mock_pipeline_instance._get_parameters_dict.return_value = {'__testing__': 12}
        eq_('12 == 12', handler._prepare_conditional('{__testing__} == 12', mock_pipeline_instance, MagicMock()))

    def test_get_attribute_trait(self):
        handler = RemoteNotificationHandler()
        eq_(2, handler._get_attribute_trait(MagicMock(testing=MagicMock(trial=2)), 'testing.trial'))

    def test_evaluate_condition(self):
        handler = RemoteNotificationHandler()
        eq_('2 == 2 and 1 == 1 and 4 == 4',
            handler._prepare_conditional('pipelineInstance.status_id == 2 and actionInstance.action.id == 1 and actionInstance.status_id == 4',
                                         MagicMock(status_id=2),
                                         MagicMock(action=MagicMock(id=1),
                                                   status_id=4)))

    def test_passes_conditional_passes(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance.get_parameters_dict.return_value = {}

        ok_(handler.passes_conditional(mock_pipeline_instance,
                                       MagicMock(action=MagicMock(id=1),
                                                 status_id=4),
                                       'pipelineInstance.status_id == 2 and actionInstance.action.id == 1 and actionInstance.status_id == 4'))

    def test_passes_conditional_fails(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance.get_parameters_dict.return_value = {}

        ok_(not handler.passes_conditional(mock_pipeline_instance,
                                           MagicMock(action=MagicMock(id=1),
                                                     status_id=4),
                                           'pipelineInstance.status_id == 1 and actionInstance.action.id == 1 and actionInstance.status_id == 4'))

    def test_passes_conditional_complex_passes(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance._get_parameters_dict.return_value = {'__testing__': 2, '__trial__': 'True'}

        ok_(handler.passes_conditional(mock_pipeline_instance,
                                       MagicMock(),
                                       'pipelineInstance.status_id == 2 and {__testing__} == 2 and {__trial__}'))

    def test_passes_conditional_complex_fails(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance._get_parameters_dict.return_value = {'__testing__': 2, '__trial__': 'True'}

        ok_(not handler.passes_conditional(mock_pipeline_instance,
                                       MagicMock(),
                                       'pipelineInstance.status_id == 2 && {__testing__} == 1 && {__trial__}'))

    def test_passes_conditional_complex_or_passes(self):
        handler = RemoteNotificationHandler()
        mock_pipeline_instance = MagicMock(status_id=2)
        mock_pipeline_instance.get_parameters_dict.return_value = {'__testing__': 2, '__trial__': 'True'}

        ok_(not handler.passes_conditional(mock_pipeline_instance,
                                           MagicMock(),
                                           '(pipelineInstance.status_id == 2 && {__testing__} == 1) || {__trial__}'))
