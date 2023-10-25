from unittest import TestCase
from unittest.mock import patch

from mock import Mock

from rapid.workflow.queue_handlers.handlers.standard_queue_handler import StandardQueueHandler
from rapid.lib.queue_handler_constants import QueueHandlerConstants


class TestStandardQueueHandler(TestCase):
    def setUp(self):
        self.mock_config = Mock()
        self.mock_service = Mock()
        self.mock_flask = Mock()
        self.handler = StandardQueueHandler(self.mock_config, self.mock_service, self.mock_flask)

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

    @patch.object(StandardQueueHandler, StandardQueueHandler.can_process_action_instance.__name__)
    @patch.object(StandardQueueHandler, StandardQueueHandler.process_action_instance.__name__)
    def test_verify_still_working_contract(self, mock_process, mock_can_process):
        instances = [Mock(), Mock()]
        mock_can_process.side_effect = [False, True]
        mock_process.side_effect = Exception()

        self.assertEqual([instances[1]], self.handler.verify_still_working(instances, []))

        mock_process.assert_called_with(instances[1], [])
        mock_can_process.assert_called_with(instances[1])

