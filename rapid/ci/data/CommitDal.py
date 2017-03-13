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
from rapid.lib.Constants import ModuleConstants
from rapid.lib.framework.Injectable import Injectable

try:
    import simplejson as json
except:
    import json

from sqlalchemy.sql.expression import desc

from rapid.lib.Exceptions import DatabaseException, InvalidObjectException
from rapid.master.data.database import get_db_session
from rapid.ci.data.models import Commit, Version, CommitParameters, Vcs, PipelineInstanceCommit


class CommitDal(object):
    def get_by_identifier(self, commit_identifier):
        for session in get_db_session():
            try:
                commit = session.query(Commit).filter(Commit.commit_identifier == commit_identifier).first()
                return commit.serialize
            except:
                pass
        return None

    def create_version_for_commit(self, commit_identifier, data_version):
        for session in get_db_session():
            commit = session.query(Commit).filter(Commit.commit_identifier == commit_identifier).first()
            if commit:
                version = session.query(Version).filter(Version.name == data_version).first()
                if not version:
                    version = Version(commit_id=commit.id, name=data_version)
                    session.add(version)
                    session.commit()
                    return json.dumps(version.serialize())
                else:
                    raise DatabaseException("Version already exists", code=400)
            else:
                raise DatabaseException("Invalid commit", code=404)

    def get_versions(self, commit_identifier, latest_only=False):
        for session in get_db_session():
            commit = session.query(Commit).filter(Commit.commit_identifier == commit_identifier).first()
            if commit:
                versions = []
                query = session.query(Version).filter(Version.commit_id == commit.id).order_by(desc(Version.date_created))
                if latest_only:
                    version = query.first()
                    if version is not None:
                        return version.serialize
                    else:
                        return None
                else:
                    for version in query.all():
                        versions.append(version.serialize)
                return versions
            else:
                raise DatabaseException("Invalid commit identifier")

    def _get_or_create_commit(self, commit_identifier, session, vcs_id):

        commit = session.query(Commit).filter(Commit.commit_identifier == commit_identifier).first()

        if not commit:
            commit = Commit(commit_identifier=commit_identifier, vcs_id=vcs_id)
            session.add(commit)
        return commit

    def create_git_commit(self, commit_identifier, vcs_id, additional_info=None, pipeline_instance_id=None, session=None):
        if session is None:
            for session in get_db_session():
                self._create_git_commit(commit_identifier, additional_info, pipeline_instance_id, session, True, vcs_id)
        else:
            self._create_git_commit(commit_identifier, additional_info, pipeline_instance_id, session, False, vcs_id)

    def _create_git_commit(self, commit_identifier, additional_info, pipeline_instance_id, session, should_commit, vcs_id):
        if commit_identifier:
            commit = self._get_or_create_commit(commit_identifier, session, vcs_id)
            if additional_info:
                for key, value in additional_info.iteritems():
                    parameter = CommitParameters(commit_id=commit.id, name=key, value=value)
                    session.add(parameter)

            if pipeline_instance_id:
                session.flush()
                session.add(PipelineInstanceCommit(pipeline_instance_id=pipeline_instance_id, commit_id=commit.id))

            if should_commit:
                session.commit()
            return commit.serialize
        raise InvalidObjectException("Commit Identifier required.")

    def get_vcs_by_repo_name(self, repo_name):
        for session in get_db_session():
            vcs = session.query(Vcs).filter(Vcs.name == repo_name).first()
            return vcs.serialize() if vcs is not None else None

    def get_vcs_by_pipeline_id(self, pipeline_id, session=None):
        if session:
            vcs = session.query(Vcs).filter(Vcs.pipeline_id == pipeline_id).first()
            return vcs.serialize() if vcs is not None else None
        else:
            for session in get_db_session():
                vcs = session.query(Vcs).filter(Vcs.pipeline_id == pipeline_id).first()
                return vcs.serialize() if vcs is not None else None
