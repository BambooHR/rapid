import datetime
import logging
import json
import re

import boto3

from rapid.lib.constants import Constants
from rapid.lib.framework.injectable import Injectable
from rapid.lib.work_request import WorkRequest
from rapid.master.master_configuration import MasterConfiguration
from rapid.workflow.action_instances_service import ActionInstanceService
from rapid.workflow.queue_handlers.container_handlers.container_handler import ContainerHandler
from rapid.workflow.queue_handlers.container_handlers.ecs_configuration import ECSConfiguration
from rapid.workflow.queue_handlers.queue_handler_constants import register_queue_handler

logger = logging.getLogger('rapid')


@register_queue_handler
class ECSQueueHandler(ContainerHandler, Injectable):
    __injectables__ = {'rapid_config': None, 'action_instance_service': ActionInstanceService}
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
        # 1. Get the Task Definition
        task_definition = self._get_task_definition(work_request)

        if 'taskDefinition' not in task_definition:
            self._set_task_status(work_request.action_instance_id, Constants.STATUS_FAILED,
                                  start_date=datetime.datetime.utcnow(),
                                  end_date=datetime.datetime.utcnow())
        else:
            # 2. Set the status to INProgress
            self._set_task_status(work_request.action_instance_id, Constants.STATUS_INPROGRESS, start_date=datetime.datetime.utcnow())

            # 3. Run the task
            (status_id, assigned_to) = self._run_task(task_definition)

            # 4. Report the status
            self._set_task_status(work_request.action_instance_id, status_id, assigned_to)
        return True

    def process_action_instance(self, action_instance, clients):
        # TODO - Still to do for handling long running requests.
        # 1. Look at the assigned_to for the specific ARN
        # 2. Verify that the assigned_to ARN is running.
        # 3. Introduce a time limit?
        pass

    ########################
    # Private Methods
    ########################

    def _get_task_definition(self, work_request):
        task_definition = self._get_overridden_task_definition(work_request.configuration)
        self._inject_work_request_parameters(task_definition, work_request)
        return task_definition

    def _get_overridden_task_definition(self, configuration):
        # type: (str) -> dict
        task_definition = self._ecs_configuration.default_task_definition
        try:
            for key, value in json.loads(configuration).items():
                task_definition[key] = value
        except ValueError as exception:
            logger.exception(exception)

        return task_definition

    def _inject_work_request_parameters(self, task_definition, work_request):
        # type:(dict, WorkRequest) -> None
        environment_default = [{'name': 'action_instance_id', 'value': work_request.action_instance_id},
                               {'name': 'workflow_instance_id', 'value': work_request.workflow_instance_id},
                               {'name': 'pipeline_instance_id', 'value': work_request.pipeline_instance_id}]

        container_overrides = self._get_task_definition_key(task_definition, 'overrides:dict.containerOverrides:[]')
        container_overrides.append({"environment": environment_default})

        (grain_type, image) = self._get_grain_type_split(work_request.grain)
        task_definition['taskDefinition'] = self._get_substituted_value(work_request, image.strip())
        task_definition['count'] = 1

    @staticmethod
    def _get_task_definition_key(task_definition, in_key):
        current_pointer = None
        for tmp_key in in_key.split('.'):
            try:
                (key, default_type) = tmp_key.split(':')

                try:
                    if current_pointer is not None:
                        current_pointer = current_pointer[key]
                    else:
                        current_pointer = task_definition[key]
                except KeyError:
                    if current_pointer is not None:
                        current_pointer[key] = eval('{}()'.format(default_type))
                        current_pointer = current_pointer[key]
                    else:
                        current_pointer = eval('{}()'.format(default_type))
                        task_definition[key] = current_pointer
            except ValueError:
                pass
        return current_pointer

    def _set_task_status(self, action_instance_id, status_id, assigned_to='', start_date=None, end_date=None):
        # type: (int, int, str, datetime.datetime or None, datetime.datetime or None) -> None
        assigned_to = '--ecs--{}'.format(assigned_to)
        changes = {'status_id': status_id, 'assigned_to': assigned_to}
        if start_date:
            changes['start_date'] = start_date
        if end_date:
            changes['end_date'] = end_date
        self.action_instance_service.edit_action_instance(action_instance_id, changes)
        
    def _run_task(self, task_definition):
        ecs_client = self._get_ecs_client()
        response_dict = ecs_client.run_task(**task_definition)
        status_id = Constants.STATUS_INPROGRESS
        assigned_to = ''
        try:
            if response_dict['failures'] or not response_dict['tasks']:
                status_id = Constants.STATUS_FAILED
            elif response_dict['tasks']:
                for task in response_dict['tasks']:
                    assigned_to = '--ecs--{}'.format(task['taskArn'])
        except KeyError:
            status_id = Constants.STATUS_FAILED
        return status_id, assigned_to

    @staticmethod
    def _get_substituted_value(work_request, sub_string):
        if '{' in sub_string:
            try:
                for match in re.findall(r'{[\w_]*}', sub_string):
                    token = match.split('{')[1].split('}')[0]
                    try:
                        sub_string = sub_string.replace(match, '{}'.format(getattr(work_request, token)))
                    except AttributeError:
                        pass
            except (TypeError, AttributeError):
                pass
        return sub_string

    def _get_ecs_client(self):
        if self._ecs_client is None:
            self._ecs_client = self._load_aws_config()
        return self._ecs_client

    def _load_aws_config(self):
        self._ecs_configuration = ECSConfiguration(self.rapid_config.ecs_config_file)
        return boto3.client('ecs', **self._ecs_configuration.aws_credentials)
