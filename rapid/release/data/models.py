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
# pylint: disable=no-member,too-few-public-methods

import datetime

from sqlalchemy.orm import relationship, backref
from sqlalchemy import Column, String, ForeignKey, Integer, DateTime, Boolean, Text, Enum

from rapid.lib import get_declarative_base
from rapid.master.data.database.models.base.base_model import BaseModel
from rapid.lib.constants import VcsReleaseStepType
Base = get_declarative_base()


class Release(BaseModel, Base):
    name = Column(String(255), nullable=False, index=True)
    date_created = Column(DateTime(), nullable=False, default=datetime.datetime.utcnow, index=True)
    status_id = Column(Integer, ForeignKey('statuses.id'), nullable=False, index=True)
    commit_id = Column(Integer, ForeignKey('commits.id'), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey('integrations.id'), index=True)

    status = relationship('Status')
    integration = relationship('Integration')
    commit = relationship('Commit', backref=backref('release', uselist=False))


class StepIntegration(BaseModel, Base):
    step_id = Column(Integer, ForeignKey('steps.id'), nullable=False, index=True)
    integration_id = Column(Integer, ForeignKey('integrations.id'), nullable=False, index=True)


class Step(BaseModel, Base):
    name = Column(String(100), nullable=False)
    custom_id = Column(String(25), nullable=False)
    status_id = Column(Integer, ForeignKey('statuses.id'), nullable=False, index=True)
    user_required = Column(Boolean, default=False, nullable=False)
    release_id = Column(Integer, ForeignKey('releases.id'), nullable=False, index=True)
    sort_order = Column(Integer, default=0)

    release = relationship("Release", lazy='subquery', backref="steps")
    status = relationship('Status')
    integrations = relationship("Integration", secondary="step_integrations")


class StepUser(BaseModel, Base):
    step_id = Column(Integer, ForeignKey('steps.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    date_created = Column(DateTime(), nullable=False, default=datetime.datetime.utcnow)


class StepUserComment(BaseModel, Base):
    step_user_id = Column(Integer, ForeignKey('step_users.id'), nullable=False)
    comment = Column(Text)


class User(BaseModel, Base):
    name = Column(String(150), nullable=False)
    username = Column(String(150), nullable=False)
    active = Column(Boolean, default=True, nullable=False)


class VcsRelease(BaseModel, Base):
    search_filter = Column(String(500), nullable=False)
    notification_id = Column(String(250), nullable=False)
    vcs_id = Column(Integer, ForeignKey('vcs.id'), nullable=False, index=True)
    auto_release = Column(Boolean, nullable=False, default=False)

    vcs = relationship('Vcs', lazy='subquery', backref='product_release')
    steps = relationship("VcsReleaseStep", backref='vcs_release')


class VcsReleaseStep(BaseModel, Base):
    name = Column(String(250), nullable=False)
    custom_id = Column(String(250), nullable=False)
    user_required = Column(Boolean, default=False, nullable=False)
    sort_order = Column(Integer, default=0)
    type = Column(Enum(*list(map(lambda x: x.name, VcsReleaseStepType))), nullable=False, default='PRE')
    vcs_release_id = Column(Integer, ForeignKey('vcs_releases.id'), nullable=False, index=True)


__all__ = ['Release', 'StepIntegration', 'Step', 'StepUser', 'StepUserComment', 'StepIntegration', 'User', 'VcsRelease', 'VcsReleaseStep']
