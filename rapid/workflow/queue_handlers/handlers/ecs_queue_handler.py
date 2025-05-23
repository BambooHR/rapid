import datetime
import logging
import json
import re
from typing import Dict, List, Union

import boto3
from botocore.exceptions import ClientError

from rapid.lib.constants import StatusConstants
from rapid.lib.exceptions import ECSLimitReached, QueueHandlerShouldSleep, ECSConnectionError, ECSCapacityReached, ECSServiceUnavailable
from rapid.lib.framework.injectable import Injectable
from rapid.lib.work_request import WorkRequest
from rapid.master.master_configuration import MasterConfiguration
from rapid.workflow.action_instances_service import ActionInstanceService
from rapid.workflow.queue_handlers.container_handlers.container_handler import ContainerHandler
from rapid.workflow.queue_handlers.container_handlers.ecs_configuration import ECSConfiguration
from rapid.workflow.queue_handlers.queue_handler_register import register_queue_handler

logger = logging.getLogger('rapid')


@register_queue_handler
class ECSQueueHandler(ContainerHandler, Injectable):
    _ASSIGNED_TO_PREFIX='--ecs--'
    @property
    def container_identifier(self):
        return 'ecs'

    @property
    def assigned_to_prefix(self) -> str:
        return self._ASSIGNED_TO_PREFIX

    def __init__(self, rapid_config: MasterConfiguration, action_instance_service: ActionInstanceService):
        """
        Parameters
        ----------
        rapid_config: MasterConfiguration
        action_instance_service: ActionInstanceService
        """
        super(ECSQueueHandler, self).__init__(rapid_config, action_instance_service)
        self._ecs_client = None
        self._ecs_configuration = None  # type: ECSConfiguration or None

    def process_work_request(self, work_request, clients):
        # type: (WorkRequest, list) -> bool
        # 1. Get the Task Definition
        self._get_ecs_client()  # load the client and get ready to use the taskDefinition

        task_definition = self._get_task_definition(work_request)

        if 'taskDefinition' not in task_definition:
            self._set_task_status(work_request.action_instance_id, StatusConstants.FAILED,
                                  start_date=datetime.datetime.utcnow(),
                                  end_date=datetime.datetime.utcnow())
        else:
            try:
                # 2. Run the Task
                (status_id, assigned_to) = self._run_task(task_definition)

                # 3. Verify the status in case it failed.
                end_date = None
                if status_id > StatusConstants.INPROGRESS:
                    end_date = datetime.datetime.utcnow()

                # 3. Report the status
                if end_date:
                    self._set_task_status(work_request.action_instance_id, status_id, assigned_to, end_date=end_date)
                elif status_id != StatusConstants.READY:
                    self._set_task_status(work_request.action_instance_id, status_id, assigned_to, start_date=datetime.datetime.utcnow())
            except ECSLimitReached as limit:
                logger.error("ECSQueueHandler: Limit reached: {}".format(limit))
                raise QueueHandlerShouldSleep('ECS Limit was reached.')
            except ECSConnectionError as conn_error:
                logger.error("ECSQueueHandler: Connection issue: {}".format(conn_error))
                raise QueueHandlerShouldSleep('ECS Connection issue detected.')
            except ECSCapacityReached as capacity:
                logger.error("ECSQueueHandler: Capacity issue: {}".format(capacity))
                raise QueueHandlerShouldSleep('ECS Capacity unavailable.')
            except ECSServiceUnavailable as service_error:
                logger.error("ECSQueueHandler: Service issue: {}".format(service_error))
                raise QueueHandlerShouldSleep('ECS Service unavailable.')
            except ClientError as param_exception:
                param_str = f'{param_exception}'
                logger.error("ECSQueueHandler: ClientError: {}".format(param_exception))

                if 'RequestLimitExceeded' in param_str:
                    raise QueueHandlerShouldSleep('ECS Request Limit Exceeded')
                if 'Capacity is unavailable at this time' in param_str:
                    raise QueueHandlerShouldSleep('ECS Capacity is unavailable')
                if 'Service Unavailable.' in param_str:
                    raise QueueHandlerShouldSleep('ECS Service unavailable.')
            except Exception as exception:
                if 'Service Unavailable' in f'{exception}':
                    logger.error("ECSQueueHandler: Service Unavailable: {}".format(exception))

                    raise QueueHandlerShouldSleep('ECS Service unavailable.')
                raise
        return True

    def _get_arn(self, action_instance: dict) -> Union[str, None]:
        try:
            if action_instance and 'assigned_to' in action_instance and action_instance['assigned_to']:
                assigned_to = action_instance['assigned_to']
                if self._ASSIGNED_TO_PREFIX in assigned_to:
                    return assigned_to.split(self._ASSIGNED_TO_PREFIX, 1)[1]
        except (ValueError, TypeError, KeyError, IndexError):
            pass
        return None

    def verify_still_working(self, action_instances: List[Dict], clients):
        failed_instances = []
        tasks = -1
        for action_instance in action_instances:
            if self.can_process_action_instance(action_instance):
                if tasks == -1:
                    tasks = self._get_running_tasks()

                try:
                    arn = self._get_arn(action_instance)
                    if arn and arn not in tasks:
                        self.action_instance_service.reset_action_instance(action_instance['id'], check_status=True)
                except Exception as exception:
                    logger.error(exception)
                    failed_instances.append(action_instance)
        return failed_instances

    def _get_running_tasks(self) -> Union[List[str], None]:
        next_token = ''
        cluster = self._ecs_configuration.default_task_definition['cluster']
        _running_tasks = None
        while next_token is not None:
            tasks = self._get_ecs_client().list_tasks(cluster=cluster,
                                                      desiredStatus='RUNNING',
                                                      nextToken=next_token)
            if 'taskArns' in tasks:
                if _running_tasks is None:
                    _running_tasks = []
                _running_tasks.extend(tasks['taskArns'])
            next_token = tasks['nextToken'] if 'nextToken' in tasks else None
        return _running_tasks

    def process_action_instance(self, action_instance, clients):
        # 1. Look at the assigned_to for the specific ARN
        arn = self._get_arn(action_instance)
        tasks = self._get_running_tasks()
        if arn and tasks is not None and arn not in tasks:
            self.action_instance_service.reset_action_instance(action_instance['id'], check_status=True)

    def cancel_worker(self, action_instance):  # type: (dict) -> bool
        try:
            arn = action_instance['assigned_to'].split(self._ASSIGNED_TO_PREFIX)[1] if action_instance and action_instance['assigned_to'] else None
            if not arn:
                return False

            task = self._get_ecs_client().stop_task(cluster=self._ecs_configuration.default_task_definition['cluster'],
                                                    task=arn,
                                                    reason='Rapid canceled.')
            if 'task' in task and task['task']:
                return True

            logger.info("Failed to cancel ECS arn: {}".format(arn))
        except Exception as exception:
            logger.exception(exception)
        return False


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
            if configuration:
                for key, value in json.loads(configuration).items():
                    task_definition[key] = value
        except (ValueError, TypeError) as exception:
            logger.exception(exception)

        return task_definition

    def _inject_work_request_parameters(self, task_definition, work_request):
        # type:(dict, WorkRequest) -> None
        environment_default = self.get_default_environment(work_request)

        (grain_type, image) = self._get_grain_type_split(work_request.grain)
        container_overrides = self._get_task_definition_key(task_definition, 'overrides:dict.containerOverrides:list')
        container_overrides.append({"name": image.split(':')[0],
                                    "environment": environment_default})

        task_definition['tags'] = [{'key': 'pipeline_instance_id', 'value': f'{work_request.pipeline_instance_id}'},
                                   {'key': 'action_instance_id', 'value': f'{work_request.action_instance_id}'}]

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

    def _run_task(self, task_definition):
        ecs_client = self._get_ecs_client()
        status_id = StatusConstants.INPROGRESS
        assigned_to = ''
        try:
            response_dict = ecs_client.run_task(**task_definition)
            if response_dict['failures']:
                logger.error("Failures were found: [{}]".format(response_dict['failures']))
                reason = response_dict['failures'][0]['reason']
                if 'limit' in reason:
                    raise ECSLimitReached(reason)
                elif 'connect timed out' in reason:
                    raise ECSConnectionError(reason)
                elif 'Capacity is unavailable at this time' in reason:
                    raise ECSCapacityReached(reason)
                elif 'Service unavailable' in reason:
                    raise ECSServiceUnavailable(reason)
                else:
                    status_id = StatusConstants.FAILED
            elif not response_dict['tasks']:
                logger.error("No tasks were returned")
                status_id = StatusConstants.READY
            elif response_dict['tasks']:
                for task in response_dict['tasks']:
                    assigned_to = f'{self._ASSIGNED_TO_PREFIX}{task["taskArn"]}'
        except (KeyError, ClientError, IndexError) as exception:
            logger.error(exception)
            status_id = StatusConstants.FAILED
        
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
