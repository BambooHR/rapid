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

from rapid.ci.data.CommitDal import CommitDal
from rapid.lib.framework.Injectable import Injectable
from rapid.lib.modules.modules import CiModule


class VcsService(Injectable, CiModule):
    __injectables__ = {'commit_dal': CommitDal}

    def __init__(self, commit_dal):
        """
        :type commit_dal: :class:`rapid.ci.data.CommitDal.CommitDal`
        :return:
        """
        self.commit_dal = commit_dal

    def get_vcs_by_repo_name(self, repo_name):
        return self.commit_dal.get_vcs_by_repo_name(repo_name)

    def create_git_commit(self, commit_identifier, vcs_id, pipeline_instance_id=None, additional_parameters=None, session=None):
        """
        Create a git commit entry.
        :param commit_identifier:
        :param additional_parameters:
        :type additional_parameters: dict
        :return:
        """
        return self.commit_dal.create_git_commit(commit_identifier, vcs_id, additional_parameters, pipeline_instance_id, session)

    def create_version_for_commit(self, commit_identifier, version):
        return self.commit_dal.create_version_for_commit(commit_identifier, version)

    def get_by_identifier(self, commit_identifier):
        return self.commit_dal.get_by_identifier(commit_identifier)

    def get_vcs_by_pipeline_id(self, pipeline_id, session=None):
        return self.commit_dal.get_vcs_by_pipeline_id(pipeline_id, session)
