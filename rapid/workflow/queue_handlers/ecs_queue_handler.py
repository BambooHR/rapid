import boto3

from rapid.lib.work_request import WorkRequest
from rapid.master.master_configuration import MasterConfiguration
from rapid.workflow.action_instances_service import ActionInstanceService
from rapid.workflow.queue_handlers.container_handlers.container_handler import ContainerHandler
from rapid.workflow.queue_handlers.queue_handler import QueueHandler
from rapid.workflow.queue_handlers.queue_handler_constants import register_queue_handler


@register_queue_handler
class ECSQueueHandler(ContainerHandler):
    @property
    def container_identifier(self):
        return 'ecs'

    def __init__(self, rapid_config, action_instance_service):
        # type: (MasterConfiguration, ActionInstanceService) -> None
        super(ECSQueueHandler, self).__init__(rapid_config)
        self.action_instance_service = action_instance_service

    def process_work_request(self, work_request, clients):
        pass

    def process_action_instance(self, action_instance, clients):
        pass

    def _load_aws_config(self):
        client = boto3.client('ecs')

