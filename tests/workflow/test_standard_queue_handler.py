from unittest import TestCase

from mock import Mock

from rapid.workflow.queue_handlers.handlers.standard_queue_handler import StandardQueueHandler
from rapid.workflow.queue_handlers.queue_handler_constants import QueueHandlerConstants


class TestStandardQueueHandler(TestCase):
    def setUp(self):
        self.mock_config = Mock()
        self.mock_service = Mock()
        self.handler = StandardQueueHandler(self.mock_config, self.mock_service)

    def test_standard_queue_handler_auto_registers(self):
        self.assertTrue(StandardQueueHandler in QueueHandlerConstants.queue_handler_classes)

    def test_can_process_work_request_without_grain_split(self):
        self.assertTrue(self.handler.can_process_work_request(Mock(grain='something')))

    def test_can_process_work_request_fails_with_split(self):
        self.assertFalse(self.handler.can_process_work_request(Mock(grain="a{}b".format(self.handler._GRAIN_SPLIT))))

    def test_can_process_action_instance_without_grain_split(self):
        self.assertTrue(self.handler.can_process_action_instance({'grain': 'another'}))

    def test_can_process_action_instance_fails_with_split(self):
        self.assertFalse(self.handler.can_process_action_instance({'grain': 'a{}b'.format(self.handler._GRAIN_SPLIT)}))
