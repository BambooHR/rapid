from unittest import TestCase

from mock import Mock

from rapid.workflow.queue_handlers.handlers.docker_queue_handler import DockerQueueHandler


class TestDockerQueueHandler(TestCase):
    def setUp(self):
        self.master_config = Mock()
        self.action_instance_service = Mock()
        self.handler = DockerQueueHandler(self.master_config, self.action_instance_service)

    def test_container_identifier(self):
        self.assertEqual('docker', self.handler.container_identifier)

    
