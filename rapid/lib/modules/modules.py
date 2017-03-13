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

from abc import ABCMeta, abstractmethod


class QaModule(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def save_results(self, action_instance, session, post_data):
        yield

    @abstractmethod
    def reset_results(self, action_instance_id, session):
        """
        Reset Stacktrace and QaTestHistory entries for action_instance
        :param action_instance_id: int
        :param session:
        :return:
        """
        yield

    @abstractmethod
    def analyze_tests(self, pipeline_instance_id, json):
        """
        Analyze the Test definitions for rapid-* comments
        :param pipeline_instance_id:
        :type pipeline_instance_id: int
        :param json: JSON representation for data
        :type json: dict
        :return: dictionary
        :rtype: dict
        """
        yield

    @abstractmethod
    def get_test_results(self, action_instance_id, filters=None):
        """
        Get test results by filter
        :param action_instance_id:
        :type action_instance_id: int
        :param filters:
        :type filters: string
        :return:
        :rtype: dict
        """
        yield

    @abstractmethod
    def get_qa_testmap_coverage(self, pipeline_instance_id):
        yield


class WorkflowModule(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def start_pipeline_via_repo(self, repo_name, parameters):
        yield

    @abstractmethod
    def get_status_by_name(self, status_name, session=None):
        yield

    @abstractmethod
    def start_pipeline_by_id(self, pipeline_id, json_data=None):
        yield

    @abstractmethod
    def get_pipeline_instance_by_id(self, pipeline_instance_id):
        yield


class CiModule(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_vcs_by_repo_name(self, repo_name):
        yield

    @abstractmethod
    def create_git_commit(self, commit_identifier, vcs_id, pipeline_instance_id=None, additional_parameters=None, session=None):
        yield

    @abstractmethod
    def get_by_identifier(self, commit_identifier):
        yield

    @abstractmethod
    def get_vcs_by_pipeline_id(self, pipeline_id, session=None):
        yield
