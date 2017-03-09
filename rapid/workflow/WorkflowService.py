"""
 Copyright (c) 2015 Michael Bright and Bamboo HR LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

from rapid.lib.framework.Injectable import Injectable
from rapid.lib.modules.modules import WorkflowModule
from rapid.workflow.ActionService import ActionService


class WorkflowService(WorkflowModule, Injectable):

    __injectables__ = {'action_service': ActionService}

    def __init__(self, action_service):
        """

        :param action_service:
        :type action_service: ActionService
        """
        self.action_service = action_service

    def start_pipeline_via_repo(self, repo_name, parameters=None):
        return self.action_service.start_pipeline_via_repo(repo_name, parameters)

    def get_status_by_name(self, status_name, session=None):
        return self.action_service.get_status_by_name(status_name, session)

    def start_pipeline_by_id(self, pipeline_id, json_data=None):
        return self.action_service.start_pipeline_by_id(pipeline_id, json_data=json_data)

    def get_pipeline_instance_by_id(self, pipeline_instance_id):
        return self.action_service.get_pipeline_instance_by_id(pipeline_instance_id)

    def get_custom_report(self, report_name):
        return self.action_service.get_custom_report(report_name)

    def list_canned_reports(self):
        return self.action_service.list_canned_reports()
