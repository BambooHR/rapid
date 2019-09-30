from unittest import TestCase

from rapid.workflow.queue_handlers.container_handlers.ecs_queue_handler import ECSQueueHandler
from rapid.workflow.queue_handlers.queue_handler_constants import QueueHandlerConstants


class TestECSQueueHandler(TestCase):
    def test_ecs_queue_handler_auto_registers(self):
        self.assertTrue(ECSQueueHandler in QueueHandlerConstants.queue_handler_classes)
