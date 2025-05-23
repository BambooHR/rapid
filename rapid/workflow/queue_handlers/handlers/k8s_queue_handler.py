import datetime
import json
import logging
from typing import Dict, List, Union
from dateutil import tz

import urllib3
import yaml
from kubernetes import client, config

from rapid.lib.constants import StatusConstants
from rapid.lib.exceptions import QueueHandlerShouldSleep, K8SServiceUnavailable, K8SConnectionError
from rapid.lib.framework.injectable import Injectable
from rapid.lib.work_request import WorkRequest
from rapid.master.master_configuration import MasterConfiguration
from rapid.workflow.action_instances_service import ActionInstanceService
from rapid.workflow.queue_handlers.container_handlers.container_handler import ContainerHandler
from rapid.workflow.queue_handlers.queue_handler_register import register_queue_handler

logger = logging.getLogger('rapid')


@register_queue_handler
class K8SQueueHandler(ContainerHandler, Injectable):
    _ASSIGNED_TO_PREFIX='--k8s--'
    
    @property
    def container_identifier(self):
        return 'k8s'

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
        super(K8SQueueHandler, self).__init__(rapid_config, action_instance_service)
        self._is_loaded = False
        self._core_api_v1: client.CoreV1Api = None
        self._batch_api_v1: client.BatchV1Api = None

    def _load_k8s_client(self):
        if not self._is_loaded:
            config.load_incluster_config()
            # config.load_kube_config()
            self._is_loaded = True

    @property
    def core_api_v1(self) -> client.CoreV1Api:
        """
        Retrieves the Kubernetes CoreV1Api client.

        Returns
        -------
        client.CoreV1Api
            The CoreV1Api client.

        """
        if self._core_api_v1 is None:
            self._load_k8s_client()
            self._core_api_v1 = client.CoreV1Api()
        return self._core_api_v1

    @property
    def batch_api_v1(self) -> client.BatchV1Api:
        """
        Retrieves the Kubernetes BatchV1Api client.

        Returns
        -------
        client.BatchV1Api
            The BatchV1Api client.

        """
        if self._batch_api_v1 is None:
            self._load_k8s_client()
            self._batch_api_v1 = client.BatchV1Api()
        return self._batch_api_v1

    def _get_job_definition(self, work_request: WorkRequest) -> Union[Dict, None]:
        (grain_type, grain_name) = self._get_grain_type_split(work_request.grain)
        try:
            with open(f'{self.rapid_config.k8s_config_dir}/{grain_name}.yaml', 'r') as f:
                job = yaml.safe_load(f)
                return job
        except FileNotFoundError:
            return None

    def _job_name(self, grain_name: str, pipeline_instance_id: int, action_instance_id: int) -> str:
        # Kubernetes job names are limited to 63 characters
        job_name = f'{grain_name}-{pipeline_instance_id}.{action_instance_id}'
        if len(job_name) > 63:
            # If the name is too long, truncate the grain_name part while preserving the IDs
            # Format: <truncated_grain_name>-<pipeline_id>.<action_id>
            id_part = f'-{pipeline_instance_id}.{action_instance_id}'
            max_grain_length = 63 - len(id_part)
            job_name = f'{grain_name[:max_grain_length]}{id_part}'
        return job_name

    def _run_task(self, work_request: WorkRequest, job: Dict):
        status_id = StatusConstants.INPROGRESS
        if job and 'metadata' in job:
            job_name = work_request.action_instance_id
            try:
                
                job_name = self._job_name(job['metadata']['name'], work_request.pipeline_instance_id, work_request.action_instance_id)
                job['metadata']['name'] = job_name
                for container in job['spec']['template']['spec']['containers']:
                    container['env'] = self.get_default_environment(work_request)
                    if work_request.environment:
                        container['env'].extend([{'name': key, 'value': str(value)} for key, value in work_request.environment.items()])

                self.batch_api_v1.create_namespaced_job(namespace='cihub', body=job)
                self._set_task_status(work_request.action_instance_id, status_id, assigned_to=self._ASSIGNED_TO_PREFIX + job_name,
                                      start_date=datetime.datetime.now(tz=tz.tzutc()))
            except KeyError:
                logger.error(f'Error creating job {job_name}')
                self._set_task_status(work_request.action_instance_id, StatusConstants.FAILED,
                                      start_date=datetime.datetime.now(tz=tz.tzutc()),
                                      end_date=datetime.datetime.now(tz=tz.tzutc()))
            except client.exceptions.ApiException as exception:
                if exception.status in [422, 404]:
                    # 404 - Not found
                    # 422 - Bad Definition
                    logger.error(f"{exception.status}: {json.loads(exception.body)['message']}")
                    self._set_task_status(work_request.action_instance_id, StatusConstants.FAILED,
                                          start_date=datetime.datetime.now(tz=tz.tzutc()),
                                          end_date=datetime.datetime.now(tz=tz.tzutc()))
                elif exception.status in [409, 400]:
                    # 409 - Already exists and will not re-run.
                    # 400 - Waiting to start?
                    raise K8SServiceUnavailable(exception.body)
                else:
                    raise QueueHandlerShouldSleep("An error occurred, let's wait.")
            except urllib3.exceptions.RequestError as exception:
                raise K8SConnectionError(f"{exception}")


    def process_work_request(self, work_request: WorkRequest, clients: list):
        job = self._get_job_definition(work_request)
        if job is None:
            self._set_task_status(work_request.action_instance_id, StatusConstants.FAILED,
                                  start_date=datetime.datetime.now(tz=tz.tzutc()),
                                  end_date=datetime.datetime.now(tz=tz.tzutc()))
        else:
            try:
                self._run_task(work_request, job)
            except (K8SConnectionError, K8SServiceUnavailable) as exception:
                raise QueueHandlerShouldSleep(f"{exception}")
        return True  # Placeholder return

    def _get_running_pods(self) -> List[client.V1Pod]:
        return self.core_api_v1.list_namespaced_pod('cihub', label_selector='status=Running').items

    def verify_still_working(self, action_instances: List[Dict], clients) -> List[Dict]:
        """
        Verifies if the action instances are still working based on the clients passed in.

        Parameters
        ----------
        action_instances: List[Dict]
            A list of action instances to verify.
        clients: list
            A list of clients to check against.

        Returns
        -------
        List[Dict]
            A list of action instances that are still working.
        """
        names = []
        failed_instances = []
        running_pods: Union[List[client.V1Pod], None] = None
        for action_instance in action_instances:
            if not self.can_process_action_instance(action_instance):
                continue

            if running_pods is None:
                running_pods = self._get_running_pods()
            try:
                job_name = self._job_name(action_instance['grain'], action_instance['pipeline_instance_id'], action_instance['id'])
                pod_found = False
                for pod in running_pods:
                    if pod.metadata.labels and job_name in pod.metadata.labels.values():
                        pod_found = True
                        break
                if not pod_found:
                    self.action_instance_service.reset_action_instance(action_instance['id'], check_status=True)
            except Exception as exception:
                failed_instances.append(action_instance)

        return failed_instances


    def cancel_worker(self, action_instance) -> bool:
        """
        Cancels the worker associated with the given action instance.

        Parameters
        ----------
        action_instance: dict
            The action instance to cancel the worker for.

        Returns
        -------
        bool
            True if the worker was canceled, False otherwise.

        Raises
        ------
        K8SConnectionError
            A connection to the Kubernetes cluster cannot be established.
        K8SServiceUnavailable
            The Kubernetes service is unavailable.
        """

        try:
            job_name = action_instance['assigned_to'].split(self._ASSIGNED_TO_PREFIX)[1]
            job = self.batch_api_v1.read_namespaced_job(job_name, 'cihub')
            if job:
                try:
                    self.batch_api_v1.delete_namespaced_job(job_name, 'cihub')
                except:
                    ...
            for pod in self.core_api_v1.list_namespaced_pod('cihub', label_selector=f'job-name={job_name}').items:
                try:
                    self.core_api_v1.delete_namespaced_pod(pod.metadata.name, 'cihub')
                except:
                    ...
        except Exception as exception:
            logger.error(exception)
            pass

        self._set_task_status(action_instance['id'], StatusConstants.CANCELED)

        return True
