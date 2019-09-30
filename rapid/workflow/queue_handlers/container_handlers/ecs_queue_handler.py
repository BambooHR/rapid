import logging
import json
import boto3

from rapid.lib.constants import Constants
from rapid.lib.work_request import WorkRequest
from rapid.master.master_configuration import MasterConfiguration
from rapid.workflow.action_instances_service import ActionInstanceService
from rapid.workflow.queue_handlers.container_handlers.container_handler import ContainerHandler
from rapid.workflow.queue_handlers.container_handlers.ecs_configuration import ECSConfiguration
from rapid.workflow.queue_handlers.queue_handler_constants import register_queue_handler

logger = logging.getLogger('rapid')


@register_queue_handler
class ECSQueueHandler(ContainerHandler):
    @property
    def container_identifier(self):
        return 'ecs'

    def __init__(self, rapid_config, action_instance_service):
        """
        Parameters
        ----------
        rapid_config: MasterConfiguration
        action_instance_service: ActionInstanceService
        """
        super(ECSQueueHandler, self).__init__(rapid_config)
        self.action_instance_service = action_instance_service
        self._ecs_client = None
        self._ecs_configuration = None  # type: ECSConfiguration or None

    def process_work_request(self, work_request, clients):
        # type: (WorkRequest, list) -> bool
        ecs_client = self._get_ecs_client()
        task_definition = self.get_overridden_task_definition(work_request.configuration)
        self.inject_work_request_parameters(task_definition, work_request)

        status_id = Constants.STATUS_INPROGRESS
        assigned_to = '--ecs--'
        self.action_instance_service.edit_action_instance(work_request.action_instance_id, {'status_id': status_id, 'assigned_to': assigned_to})
        response_dict = ecs_client.run_task(**task_definition)
        try:
            if response_dict['failures'] or not response_dict['tasks']:
                status_id = Constants.STATUS_FAILED
            elif response_dict['tasks']:
                for task in response_dict['tasks']:
                    assigned_to = '--ecs--{}'.format(task['taskArn'])
        except KeyError:
            status_id = Constants.STATUS_FAILED

        self.action_instance_service.edit_action_instance(work_request.action_instance_id, {'status_id': status_id, 'assigned_to': assigned_to})
        return True

    def process_action_instance(self, action_instance, clients):
        pass

    def get_overridden_task_definition(self, configuration):
        # type: (str) -> dict
        task_definition = self._ecs_configuration.default_task_definition
        try:
            for key, value in json.loads(configuration):
                task_definition[key] = value
        except ValueError as exception:
            logger.exception(exception)

        return task_definition

    def inject_work_request_parameters(self, task_definition, work_request):
        # type:(dict, WorkRequest) -> None
        environment_default = [{'name': 'action_instance_id', 'value': work_request.action_instance_id},
                               {'name': 'pipeline_instance_id', 'value': work_request.pipeline_instance_id},
                               {'name': 'workflow_instance_id', 'value': work_request.workflow_instance_id}]
        overrides = {}
        try:
            overrides = task_definition['overrides']
        except KeyError:
            task_definition['overrides'] = overrides

        container_overrides = []
        try:
            container_overrides = overrides['containerOverrides']
        except KeyError:
            overrides['containerOverrides'] = container_overrides

        container_overrides.append({"environment": environment_default})

        (grain_type, image) = self._get_grain_type_split(work_request.grain)
        task_definition['taskDefinition'] = image.strip()
        task_definition['count'] = 1

    def _get_ecs_client(self):
        if self._ecs_client is None:
            self._ecs_client = self._load_aws_config()
        return self._ecs_client

    def _load_aws_config(self):
        self._ecs_configuration = ECSConfiguration(self.rapid_config.ecs_config_file)
        return boto3.client('ecs', **self._ecs_configuration.aws_credentials)
