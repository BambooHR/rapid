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

from rapid.lib.framework.injectable import Injectable
from rapid.workflow.action_dal import ActionDal
from rapid.workflow.data.dal.pipeline_dal import PipelineDal
from rapid.workflow.data.dal.report_dal import ReportDal


class ActionService(Injectable):
    __injectables__ = {'pipeline_dal': PipelineDal, 'action_dal': ActionDal, 'report_dal': ReportDal}

    def __init__(self, pipeline_dal, action_dal, report_dal):
        """

        :param pipeline_dal:
        :type pipeline_dal: PipelineDal
        :param action_dal:
        :type action_dal: ActionDal
        :param report_dal:
        :type report_dal: ReportDal
        """
        self.pipeline_dal = pipeline_dal
        self.action_dal = action_dal
        self.report_dal = report_dal

    def start_pipeline_via_repo(self, repo, json_data):
        """
        Start a pipeline via repository URL
        :rtype: dict
        """
        return self.pipeline_dal.start_pipeline_instance_via_reponame(repo, json_data)

    def get_status_by_name(self, name, session=None):
        return self.action_dal.get_status_by_name(name, session)

    def start_pipeline_by_id(self, pipeline_id, json_data):
        return self.pipeline_dal.start_pipeline_instances_via_pipeline_id(pipeline_id, json_data=json_data)

    def get_pipeline_instance_by_id(self, pipeline_instance_id):
        return self.pipeline_dal.get_pipeline_instance_by_id(pipeline_instance_id)

    def get_custom_report(self, report_name):
        return self.report_dal.get_canned_report(report_name)

    def list_canned_reports(self):
        return self.report_dal.get_canned_report_names()

    def cancel_pipeline_instance(self, pipeline_instance_id):
        return self.pipeline_dal.cancel_pipeline_instance(pipeline_instance_id)

    def cancel_action_instance(self, action_instance_id):
        return self.action_dal.cancel_action_instance(action_instance_id)

    def get_work_request_by_action_instance_id(self, action_instance_id):
        return self.action_dal.get_work_request_by_action_instance_id(action_instance_id)
