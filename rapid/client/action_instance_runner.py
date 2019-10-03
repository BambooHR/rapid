from flask import Flask

from rapid.client import ClientCommunicator
from rapid.client.executor import Executor
from rapid.lib.work_request import WorkRequest
from rapid.client.client_configuration import ClientConfiguration


class ActionInstanceRunner(object):

    def __init__(self, rapid_config):
        # type: (ClientConfiguration) -> None
        self.client_config = rapid_config

    def run_action_instance(self, app, action_instance_id):
        # type: (Flask, int) -> None
        communicator = ClientCommunicator(self.client_config.master_uri, self.client_config.quarantine_directory, app, self.client_config.verify_certs)
        self.client_config.is_single_use = True
        
        communicator.register(self.client_config)
        request_json = communicator.get_work_request_by_action_instance_id(action_instance_id)
        executor = Executor(WorkRequest(request_json),
                            self.client_config.master_uri,
                            workspace=self.client_config.workspace,
                            quarantine=self.client_config.quarantine_directory,
                            verify_certs=self.client_config.verify_certs,
                            rapid_config=self.client_config)
        executor.verify_work_request()
        executor.start(False)
