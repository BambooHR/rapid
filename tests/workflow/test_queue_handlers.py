from unittest import TestCase

from rapid.workflow.queue_handlers import setup_queue_handlers
from rapid.workflow.queue_handlers.handlers.docker_queue_handler import DockerQueueHandler
from rapid.workflow.queue_handlers.handlers.ecs_queue_handler import ECSQueueHandler
from rapid.workflow.queue_handlers.handlers.standard_queue_handler import StandardQueueHandler
from rapid.lib.queue_handler_constants import QueueHandlerConstants


class TestQueueHandlers(TestCase):
    def test_trial(self):
        setup_queue_handlers()
        self.assertEqual([DockerQueueHandler, ECSQueueHandler, StandardQueueHandler], QueueHandlerConstants.queue_handler_classes)
