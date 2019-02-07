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
import datetime

from sqlalchemy import Column, String, Integer, ForeignKey, desc, DateTime, Boolean
from sqlalchemy.orm import relationship

from rapid.lib import get_declarative_base
from rapid.master.data.database.models.base.base_model import BaseModel

Base = get_declarative_base()
# pylint: disable=no-member, too-few-public-methods


class Commit(BaseModel, Base):
    commit_identifier = Column(String(255), nullable=False, index=True)
    vcs_id = Column(Integer, ForeignKey('vcs.id'), nullable=False, index=True)

    pipeline_instances = relationship("PipelineInstance", backref="commit", secondary="pipeline_instance_commits", order_by=desc("created_date"))
    versions = relationship('Version', backref="commit", order_by=desc('date_created'))
    vcs = relationship('Vcs')


class CommitIntegration(BaseModel, Base):
    commit_id = Column(Integer, ForeignKey('commits.id'), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey('integrations.id'), nullable=False, index=True)


class CommitParameters(BaseModel, Base):
    commit_id = Column(Integer, ForeignKey("commits.id"), index=True)
    name = Column(String(255), nullable=False, index=True)
    value = Column(String(500), nullable=False)


class Version(BaseModel, Base):
    name = Column(String(255), nullable=False, index=True)
    commit_id = Column(Integer, ForeignKey("commits.id"))
    date_created = Column(DateTime(), nullable=False, default=datetime.datetime.utcnow)


class PipelineInstanceCommit(BaseModel, Base):
    pipeline_instance_id = Column(Integer, ForeignKey("pipeline_instances.id"), index=True, nullable=False)
    commit_id = Column(Integer, ForeignKey('commits.id'), index=True, nullable=False)


class Vcs(BaseModel, Base):
    name = Column(String(1500), nullable=False)
    repo = Column(String(500), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    vcs_type_id = Column(Integer, ForeignKey('vcs_types.id'), nullable=False)
    pipeline_id = Column(Integer, ForeignKey('pipelines.id'), index=True, nullable=True)

    vcs_type = relationship("VcsType")
    pipeline = relationship("Pipeline")


class VcsType(BaseModel, Base):
    name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
