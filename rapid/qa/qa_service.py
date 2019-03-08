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
from rapid.lib.modules import QaModule
from rapid.qa.data.dals.qa_dal import QaDal


class QaService(Injectable, QaModule):
    __injectables__ = {'qa_dal': QaDal}

    def __init__(self, qa_dal):
        """

        :param qa_dal:
        :type qa_dal: QaDal
        """
        self.qa_dal = qa_dal

    def reset_results(self, action_instance_id, session):
        return self.qa_dal.reset_results(action_instance_id, session)

    def save_results(self, action_instance, session, post_data):
        return self.qa_dal.save_results(action_instance, session, post_data)

    def get_test_results(self, action_instance_id, filters=None):
        """
        Get Test Results
        :param action_instance_id:
        :type action_instance_id: int
        :param filters:
        :type filters: string
        :return:
        :rtype:
        """
        return self.qa_dal.get_test_results(action_instance_id, filters=filters)

    def analyze_tests(self, pipeline_instance_id, json):
        """
        Override from QaModule
        :param pipeline_instance_id:
        :type pipeline_instance_id: int
        :param json:
        :type json: dict
        :return:
        :rtype: dict
        """
        return self.qa_dal.analyze_tests(pipeline_instance_id, json)

    def get_qa_testmap_coverage(self, pipeline_instance_id):
        """
        :param pipeline_instance_id:
        :type pipeline_instance_id: int
        :return:
        :rtype:
        """

        return self.qa_dal.get_qa_testmap_coverage(pipeline_instance_id)
