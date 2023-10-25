from typing import Dict, List
from unittest import TestCase

from mock import Mock

from rapid.workflow.queue_handlers.container_handlers.container_handler import ContainerHandler


class TestContainerHandler(TestCase):
    def setUp(self):
        self.container_handler = TestingContainerHandler(Mock())

    def test_get_grain_type_split_non_splitter(self):
        self.assertEqual(['not splittable'], self.container_handler._get_grain_type_split('not splittable'))

    def test_get_grain_type_split_with_splitter(self):
        self.assertEqual(['testing', 'worky!'], self.container_handler._get_grain_type_split('testing://worky!'))

    def test_can_process_work_request_with_bad_data(self):
        self.assertFalse(self.container_handler.can_process_work_request(Mock(grain='bad')))

    def test_can_process_work_request_with_good_data(self):
        self.assertTrue(self.container_handler.can_process_work_request(Mock(grain='testing://worky!')))

    def test_can_process_action_instance_with_bad_data(self):
        self.assertFalse(self.container_handler.can_process_action_instance({'grain': 'bad'}))

    def test_can_process_action_instance_with_good_data(self):
        self.assertTrue(self.container_handler.can_process_action_instance({'grain': 'testing://again!'}))


class TestingContainerHandler(ContainerHandler):
    def verify_still_working(self, action_instances: List[Dict], clients) -> List[Dict]:
        return []

    def cancel_worker(self, action_instance):
        pass

    def process_work_request(self, work_request, clients):
        pass

    def process_action_instance(self, action_instance, clients):
        pass

    @property
    def container_identifier(self):
        return 'testing'

