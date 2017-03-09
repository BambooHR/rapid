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

from sqlalchemy.orm import relationship, backref

from rapid.master.data import db
from rapid.master.data.database.models.base.BaseModel import BaseModel


class Release(BaseModel, db.Model):
    name = db.Column(db.String(255), nullable=False, index=True)
    date_created = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.utcnow, index=True)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=False, index=True)
    commit_id = db.Column(db.Integer, db.ForeignKey('commits.id'), nullable=False, index=True)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id'), index=True)

    status = relationship('Status')
    integration = relationship('Integration')
    commit = relationship('Commit', backref=backref('release', uselist=False))


class StepIntegration(BaseModel, db.Model):
    step_id = db.Column(db.Integer, db.ForeignKey('steps.id'), nullable=False, index=True)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id'), nullable=False, index=True)


class Step(BaseModel, db.Model):
    name = db.Column(db.String(100), nullable=False)
    custom_id = db.Column(db.String(25), nullable=False)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=False, index=True)
    user_required = db.Column(db.Boolean, default=False, nullable=False)
    release_id = db.Column(db.Integer, db.ForeignKey('releases.id'), nullable=False, index=True)
    sort_order = db.Column(db.Integer, default=0)

    release = relationship("Release", lazy='subquery', backref="steps")
    status = relationship('Status')
    integrations = relationship("Integration", secondary="step_integrations")


class StepUser(BaseModel, db.Model):
    step_id = db.Column(db.Integer, db.ForeignKey('steps.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date_created = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.utcnow)


class StepUserComment(BaseModel, db.Model):
    step_user_id = db.Column(db.Integer, db.ForeignKey('step_users.id'), nullable=False)
    comment = db.Column(db.Text)


class User(BaseModel, db.Model):
    name = db.Column(db.String(150), nullable=False)
    username = db.Column(db.String(150), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)