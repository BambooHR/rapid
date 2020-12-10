from unittest import TestCase

from mock import patch, Mock

from rapid.lib.constants import StatusConstants
from rapid.lib.exceptions import QueueHandlerShouldSleep
from rapid.lib.framework.injectable import Injectable
from rapid.workflow.queue import Queue
from rapid.workflow.queue_handlers.queue_handler import QueueHandler


class TestQueue(TestCase):
    def test_setup_queue_handlers_fires_correctly(self):
        test_queue = Queue(Mock(), Mock(), Mock(), Mock(queue_handlers=[TestQueueHandler(Mock(), Mock())]), Mock())
        self.assertTrue(isinstance(test_queue.queue_handlers[0], TestQueueHandler))

    def test_process_queue_will_process_appropriately(self):
        mock_queue_service = Mock()
        good_mock = Mock(foo='good')
        mock_queue_service.get_current_work.return_value = [Mock(foo='bad'), good_mock]
        queue = Queue(mock_queue_service, Mock(), Mock(), Mock(queue_handlers=[TestQueueHandler(Mock(), Mock())]), Mock())

        check = Mock()
        check.side_effect = [False, True]
        
        mock_handler = Mock()
        queue.queue_handlers[0].check = check
        queue.queue_handlers[0].process = mock_handler.mock

        queue.process_queue([])
        mock_handler.mock.assert_called_with(good_mock)

    @patch('rapid.workflow.queue.logger')
    @patch('rapid.workflow.queue.datetime')
    def test_process_queue_will_process_when_exception_raises(self, datetime, logger):
        mock_queue_service = Mock()
        good_mock = Mock(foo='good', action_instance_id='1234')
        bad_mock = Mock(foo='bad')
        mock_queue_service.get_current_work.return_value = [good_mock, bad_mock]
        mock_action_service = Mock()
        queue = Queue(mock_queue_service, mock_action_service, Mock(), Mock(queue_handlers=[TestQueueHandler(Mock(), Mock())]), Mock())

        check = Mock()
        check.side_effect = [True, False]

        mock_handler = Mock()
        mock_handler.mock.side_effect = Exception()

        queue.queue_handlers[0].check = check
        queue.queue_handlers[0].process = mock_handler.mock

        datetime.utcnow.return_value = 'something_wicked_this_way_comes'

        queue.process_queue([])
        check.assert_called_with(bad_mock)
        mock_action_service.edit_action_instance.assert_called_with('1234', {'status_id': StatusConstants.FAILED,
                                                                             'start_date': 'something_wicked_this_way_comes',
                                                                             'end_date': 'something_wicked_this_way_comes'})

    def test_verify_still_working_processes_appropriately(self):
        mock_queue_service = Mock()
        good_mock = {'foo': 'good'}
        mock_queue_service.get_verify_working.return_value = [{'foo': 'bad'}, good_mock]
        queue = Queue(mock_queue_service, Mock(), Mock(), Mock(queue_handlers=[TestQueueHandler(Mock(), Mock())]), Mock())

        check = Mock()
        check.side_effect = [False, True]

        mock_handler = Mock()
        queue.queue_handlers[0].check = check
        queue.queue_handlers[0].process = mock_handler.mock

        queue.verify_still_working([])
        mock_handler.mock.assert_called_with(good_mock)

    @patch('rapid.workflow.queue.logger')
    @patch('rapid.workflow.queue.datetime')
    def test_verify_still_workign_when_exception_raises(self, datetime, logger):
        mock_queue_service = Mock()
        good_mock = {'foo': 'good', 'action_instance_id': '1234', 'id': '4321'}
        bad_mock = {'foo': 'bad', 'id': 'foo_id'}
        mock_queue_service.get_verify_working.return_value = [good_mock, bad_mock]
        mock_action_service = Mock()
        queue = Queue(mock_queue_service, mock_action_service, Mock(), Mock(queue_handlers=[TestQueueHandler(Mock(), Mock())]), Mock())

        check = Mock()
        check.side_effect = [True, False]

        mock_handler = Mock()
        mock_handler.mock.side_effect = Exception()

        queue.queue_handlers[0].check = check
        queue.queue_handlers[0].process = mock_handler.mock

        datetime.utcnow.return_value = 'you_did_what?'

        queue.verify_still_working([])
        check.assert_called_with(bad_mock)
        mock_action_service.edit_action_instance.assert_called_with('4321', {'status_id': StatusConstants.FAILED,
                                                                             'start_date': 'you_did_what?',
                                                                             'end_date': 'you_did_what?'})

    def test_queue_handlers_can_be_slept(self):
        mock_handler = Mock(handler=1)
        mock_handler.can_process_work_request.return_value = True
        mock_handler.process_work_request.side_effect = QueueHandlerShouldSleep

        mock_queue_service = Mock()
        mock_queue_service.get_current_work.return_value = [1, 2]

        queue = Queue(mock_queue_service, Mock(), Mock(), Mock(queue_handlers=[mock_handler]), Mock())
        queue.process_queue([])

        self.assertEqual(1, mock_handler.can_process_work_request.call_count)
        mock_handler.can_process_work_request.assert_called_with(1)


class TestQueueHandler(QueueHandler, Injectable):
    def cancel_worker(self, action_instance):
        pass

    def __init__(self, rapid_config: Mock, action_instance_service: Mock):
        super(TestQueueHandler, self).__init__(rapid_config)
        self.action_instance_service = action_instance_service
        self.check = None
        self.process = None

    def process_work_request(self, work_request, clients):
        self.process(work_request)

    def can_process_work_request(self, work_request):
        return self.check(work_request)

    def process_action_instance(self, action_instance, clients):
        self.process(action_instance)

    def can_process_action_instance(self, action_instance):
        return self.check(action_instance)
