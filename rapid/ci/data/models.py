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

from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import desc

from rapid.master.data import db
from rapid.master.data.database.models.base.BaseModel import BaseModel


class Commit(BaseModel, db.Model):
    commit_identifier = db.Column(db.String(255), nullable=False, index=True)
    vcs_id = db.Column(db.Integer, db.ForeignKey('vcs.id'), nullable=False, index=True)

    pipeline_instances = relationship("PipelineInstance", backref="commit", secondary="pipeline_instance_commits", order_by=desc("created_date"))
    versions = relationship('Version', backref="commit", order_by=desc('date_created'))
    vcs = relationship('Vcs')


class CommitIntegration(BaseModel, db.Model):
    commit_id = db.Column(db.Integer, db.ForeignKey('commits.id'), nullable=False, index=True)
    integration_id = db.Column(db.Integer, db.ForeignKey('integrations.id'), nullable=False, index=True)


class CommitParameters(BaseModel, db.Model):
    commit_id = db.Column(db.Integer, db.ForeignKey("commits.id"), index=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    value = db.Column(db.String(500), nullable=False)


class VcsType(BaseModel, db.Model):
    name = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)


class Vcs(BaseModel, db.Model):
    name = db.Column(db.String(1500), nullable=False)
    repo = db.Column(db.String(500), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    vcs_type_id = db.Column(db.Integer, db.ForeignKey('vcs_types.id'), nullable=False)
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'), index=True, nullable=True)

    vcs_type = relationship("VcsType")
    pipeline = relationship("Pipeline")


class Version(BaseModel, db.Model):
    name = db.Column(db.String(255), nullable=False, index=True)
    commit_id = db.Column(db.Integer, db.ForeignKey("commits.id"))
    date_created = db.Column(db.DateTime(), nullable=False, default=datetime.datetime.utcnow)


class PipelineInstanceCommit(BaseModel, db.Model):
    pipeline_instance_id = db.Column(db.Integer, db.ForeignKey("pipeline_instances.id"), index=True, nullable=False)
    commit_id = db.Column(db.Integer, db.ForeignKey('commits.id'), index=True, nullable=False)
