import subprocess

import os

import yaml
from yaml.scanner import ScannerError

from rapid.lib.constants import StatusConstants
from rapid.lib.features import Features
from rapid.lib.framework.injectable import Injectable
from rapid.lib.work_request import WorkRequest
from rapid.master.master_configuration import MasterConfiguration
from rapid.workflow.action_instances_service import ActionInstanceService
from rapid.workflow.queue_handlers.container_handlers.container_handler import ContainerHandler
from rapid.workflow.queue_handlers.container_handlers.docker_configuration import DockerConfiguration
from rapid.workflow.queue_handlers.queue_handler_register import register_queue_handler


@register_queue_handler
class DockerQueueHandler(ContainerHandler, Injectable):
    __injectables__ = {'rapid_config': None, 'action_instance_service': ActionInstanceService}
    
    @property
    def container_identifier(self):
        return 'docker'

    def __init__(self, rapid_config, action_instance_service):
        # type: (MasterConfiguration, ActionInstanceService) -> None
        super(DockerQueueHandler, self).__init__(rapid_config)
        self.action_instance_service = action_instance_service

    def process_action_instance(self, action_instance, clients):
        # TODO - Still don't know how to verify this is working.
        pass

    def process_work_request(self, work_request, clients):
        # type: (WorkRequest, list) -> bool
        stdout = subprocess.PIPE
        stderr = subprocess.STDOUT

        (grain_type, image) = self._get_grain_type_split(work_request.grain)

        command = "docker run {} {}".format(
            self._get_docker_parameters(work_request),
            image
        )
        assignment = {
            'assigned_to': 'docker://',
            'status_id': StatusConstants.INPROGRESS
        }
        try:
            child_process = subprocess.Popen(command.split(' '), stderr=stderr, stdout=stdout)
            if child_process.poll():
                raise OSError('Something went wrong')
        except OSError:
            assignment['status_id'] = StatusConstants.FAILED
        self.action_instance_service.edit_action_instance(work_request.action_instance_id, assignment)
        return assignment['status_id'] == StatusConstants.INPROGRESS

    def _get_docker_parameters(self, work_request):
        try:
            docker_configuration = DockerConfiguration(**yaml.safe_load(work_request.configuration))
            return docker_configuration.get_string_rep(work_request)
        except (TypeError, AttributeError, ScannerError):
            pass

        return ''

    def get_environment(self, work_request):
        environment = {}
        for key in os.environ:
            environment[key] = os.environ[key]

        if work_request.environment:
            for key, value in work_request.environment.items():
                try:
                    environment[key.encode('ascii', 'ignore')] = value.encode('ascii', 'ignore')
                except AttributeError:
                    pass
        environment['PYTHONUNBUFFERED'] = "true"
        environment['pipeline_instance_id'] = str(work_request.pipeline_instance_id)
        environment['action_instance_id'] = str(work_request.action_instance_id)
        environment['workflow_instance_id'] = str(work_request.workflow_instance_id)
        environment['slice'] = str(work_request.slice)
        environment['RAPID_FEATURES'] = ",".join(Features.get_enabled_features())
        environment['WORKSPACE'] = self.rapid_config.workspace

        return environment

    def cancel_worker(self, action_instance):  # type: (dict) -> bool
        return True
