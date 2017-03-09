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

from sqlalchemy.orm import joinedload_all

from rapid.ci.data.models import Commit
from rapid.lib.Constants import ModuleConstants, StatusConstants, status_type_severity_mapping
from rapid.lib.framework.Injectable import Injectable
from rapid.master.data.database import get_db_session
from rapid.release.data.models import Step, Release

import logging
logger = logging.getLogger("rapid")


class ReleaseDal(Injectable):
    __injectables__ = {ModuleConstants.WORKFLOW_MODULE: None, ModuleConstants.CI_MODULE: None}

    def __init__(self, workflow_module, ci_module):
        """

        :type workflow_module: :class:`rapid.lib.modules.modules.WorkflowModule`
        :type ci_module: :class:`rapid.lib.modules.modules.CiModule`
        :return:
        """
        self.workflow_module = workflow_module
        self.ci_module = ci_module

    def get_release_by_id(self, release_id, session=None):
        if session is None:
            for session in get_db_session():
                query = session.query(Release).fitler(Release.id == release_id).first().serialize()
        else:
            return session.query(Release).filter(Release.id == release_id).first()

    def set_release_step(self, release_id, step_id, status, session=None):
        assert release_id is not None
        assert step_id is not None
        assert status is not None

        if session is None:
            for db_session in get_db_session():
                release = self.get_release_by_id(release_id, db_session)
                status_entry = self.workflow_module.get_status_by_name(status, db_session)

                if status_entry and status_entry.id:
                    found_step = self._set_internal_release_step(release_id, step_id, status, db_session)

                    self._finish_release_if_necessary(release, step_id, status_entry)

                    db_session.commit()
                    if found_step is not None:
                        return found_step.serialize()
        else:
            status_entry = self.workflow_module.get_status_by_name(status, session)
            if status_entry and status_entry.id:
                release = self.get_release_by_id(release_id, session)
                step = self._set_internal_release_step(release_id, step_id, status, session).serialize()

                self._finish_release_if_necessary(release, step_id, status_entry)
                return step
        return None

    def _finish_release_if_necessary(self, release, step_id, status_entry):
        count_complete = 0
        found_step = None
        highest_status = None
        for step in release.steps:
            if step.custom_id == step_id:
                step.status_id = status_entry.id
                found_step = step
            if step.status_id >= StatusConstants.SUCCESS:
                count_complete += 1
                if step.status.type in status_type_severity_mapping:
                    if highest_status is None or status_type_severity_mapping[highest_status.type] > status_type_severity_mapping[step.status.type]:
                        highest_status = step.status

        if count_complete == len(release.steps):
            release.status_id = highest_status.id if highest_status is not None else StatusConstants.SUCCESS
        elif release.status_id < StatusConstants.SUCCESS:
            release.status_id = StatusConstants.INPROGRESS
        return found_step

    def _set_internal_release_step(self, release_id, step_id, status, session):
        status_entry = self.workflow_module.get_status_by_name(status, session)
        if status_entry and status_entry.id:
            step = self.get_step_by_release_and_step_id(release_id, step_id, session)
            if step and step.id:
                step.status_id = status_entry.id
                return step
        raise Exception("Something didn't work!")

    def get_step_by_release_and_step_id(self, release_id, step_id, session=None):
        if session is not None:
            return session.query(Step).filter(Step.release_id == release_id)\
                .filter(Step.custom_id == step_id).first()
        else:
            return session.query(Step).filter(Step.release_id == release_id) \
                .filter(Step.custom_id == step_id).first().serialize()

    def get_release_by_commit_identifier(self, commit_identifier, session=None):
        if session is None:
            for session in get_db_session():
                release = session.query(Release).filter(Release.commit_id == Commit.id)\
                    .filter(Commit.commit_identifier == commit_identifier).first()
                return release.serialize() if release is not None else None
        else:
            return session.query(Release).filter(Release.commit_id == commit_identifier).first()

    def mark_step_for_commit(self, commit_identifier, step_custom_id, status_name):
        commit = self.ci_module.get_by_identifier(commit_identifier)
        if commit is not None:
            for session in get_db_session():
                release = self.get_release_by_commit_identifier(commit_identifier)
                if release is not None:
                    step = self.set_release_step(release.id, step_custom_id, status_name, session)
                    session.commit()
                    return step
                else:
                    logger.debug("Step is not the head of the release.")
