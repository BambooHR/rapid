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

from rapid.lib.Constants import StatusConstants
from rapid.lib.Converters import ObjectConverter
from rapid.master.data import db
from sqlalchemy.orm import relationship
from rapid.master.data.database.models.base.BaseModel import BaseModel
from rapid.master.data.database.models.base.DateModel import DateModel
from rapid.master.data.database.models.base.ActiveModel import ActiveModel


class Action(db.Model, BaseModel):
    cmd = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    executable = db.Column(db.String(100), nullable=False)
    args = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, nullable=False, index=True)
    manual = db.Column(db.Boolean, default=False, nullable=False)
    callback_required = db.Column(db.Boolean, default=False, nullable=False)
    grain = db.Column(db.String(100))
    slices = db.Column(db.Integer, default=0)

    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False, index=True)
    pipeline_id = db.Column(db.Integer, db.ForeignKey("pipelines.id"), nullable=False, index=True)

    def convert_to_instance(self):
        action_instance = ActionInstance()
        action_instance.status_id = StatusConstants.NEW
        action_instance.action_id = self.id

        return ObjectConverter.copy_attributes(self, action_instance, ['cmd',
                                                                       'executable',
                                                                       'args',
                                                                       'order',
                                                                       'manual',
                                                                       'callback_required',
                                                                       'grain'])


class ActionInstance(db.Model, DateModel, BaseModel):
    cmd = db.Column(db.String(255), nullable=False)
    executable = db.Column(db.String(100), nullable=False)
    args = db.Column(db.String(255), nullable=False)
    order = db.Column(db.Integer, nullable=False, default=0, index=True)
    manual = db.Column(db.Boolean, nullable=False, default=False)
    callback_required = db.Column(db.Boolean, nullable=False, default=False)
    grain = db.Column(db.String(100))
    assigned_to = db.Column(db.String(75), nullable=True)
    slice = db.Column(db.String(25), default='')

    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=False, index=True)
    action_id = db.Column(db.Integer, db.ForeignKey('actions.id'), nullable=False, index=True)

    workflow_instance_id = db.Column(db.Integer, db.ForeignKey('workflow_instances.id'), nullable=False, index=True)
    pipeline_instance_id = db.Column(db.Integer, db.ForeignKey("pipeline_instances.id"), nullable=False, index=True)

    status = relationship('Status')
    pipeline_instance = relationship('PipelineInstance')
    action = relationship('Action')


class IntegrationType(BaseModel, db.Model):
    name = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)


class IntegrationKeys(BaseModel, db.Model):
    name = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)


class Integration(BaseModel, db.Model):
    integration_type_id = db.Column(db.Integer, db.ForeignKey('integration_types.id'), nullable=False)
    integration_keys_id = db.Column(db.Integer, db.ForeignKey('integration_keys.id'), nullable=False)
    value = db.Column(db.String(500), nullable=False)


class Pipeline(ActiveModel, db.Model):
    stages = relationship("Stage", backref="pipeline", order_by="asc(Stage.order)")

    def convert_to_instance(self):
        instance = PipelineInstance()
        instance.pipeline_id = self.id
        return ObjectConverter.copy_attributes(self, instance, [])


class PipelineInstance(BaseModel, DateModel, db.Model):
    pipeline_id = db.Column(db.Integer, db.ForeignKey('pipelines.id'), nullable=False, index=True)
    status_id = db.Column(db.Integer, db.ForeignKey('statuses.id'), nullable=False, index=True)
    priority = db.Column(db.Integer, default=0, index=True)

    stage_instances = relationship("StageInstance", backref="pipeline_instance", order_by="asc(StageInstance.order)")
    parameters = relationship('PipelineParameters', backref="pipeline_instance")
    stats = relationship('PipelineStatistics', backref="pipeline_instance")
    pipeline = relationship('Pipeline')
    status = relationship('Status')


class PipelineParameters(BaseModel, db.Model):
    pipeline_instance_id = db.Column(db.Integer, db.ForeignKey("pipeline_instances.id"), nullable=False, index=True)
    parameter = db.Column(db.String(200), nullable=False, index=True)
    value = db.Column(db.String(4000), nullable=False)


class PipelineStatistics(BaseModel, db.Model):
    pipeline_instance_id = db.Column(db.Integer, db.ForeignKey("pipeline_instances.id"), nullable=False, index=True)
    statistics_id = db.Column(db.Integer, db.ForeignKey("statistics.id"), nullable=False, index=True)
    value = db.Column(db.Integer, nullable=False)

    statistics = relationship('Statistics', backref="pipeline_statistics")


class Stage(ActiveModel, db.Model):
    order = db.Column(db.Integer, nullable=False, default=0, index=True)
    pipeline_id = db.Column(db.Integer, db.ForeignKey("pipelines.id"), nullable=False, index=True)

    workflows = relationship("Workflow", backref="stage")

    def convert_to_instance(self):
        instance = StageInstance()
        instance.status_id = StatusConstants.NEW
        instance.stage_id = self.id
        instance.start_date = datetime.datetime.utcnow()
        return ObjectConverter.copy_attributes(self, instance, ['order'])


class StageInstance(BaseModel, DateModel, db.Model):
    order = db.Column(db.Integer, nullable=False, default=0, index=True)
    status_id = db.Column(db.Integer, db.ForeignKey("statuses.id"), nullable=False, index=True)
    pipeline_instance_id = db.Column(db.Integer, db.ForeignKey("pipeline_instances.id"), nullable=False, index=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stages.id"), nullable=False, index=True)

    stage = relationship('Stage')
    status = relationship('Status')

    workflow_instances = relationship("WorkflowInstance", backref="stage_instance", order_by="asc(WorkflowInstance.order)")


class Statistics(ActiveModel, db.Model):
    pass


class Status(ActiveModel, db.Model):
    type = db.Column(db.String(50), nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)


class Workflow(ActiveModel, db.Model):
    order = db.Column(db.Integer, nullable=False, default=0, index=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stages.id"), nullable=False, index=True)

    actions = relationship("Action", backref="workflow", order_by="asc(Action.order)")

    def convert_to_instance(self):
        instance = WorkflowInstance()
        instance.status_id = StatusConstants.NEW
        instance.workflow_id = self.id
        instance.start_date = datetime.datetime.utcnow()
        return ObjectConverter.copy_attributes(self, instance, ['order'])


class WorkflowInstance(BaseModel, DateModel, db.Model):
    order = db.Column(db.Integer, nullable=False, default=0, index=True)
    status_id = db.Column(db.Integer, db.ForeignKey("statuses.id"), nullable=False, index=True)
    stage_instance_id = db.Column(db.Integer, db.ForeignKey("stage_instances.id"), nullable=False, index=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False, index=True)

    status = relationship('Status')
    workflow = relationship('Workflow')
    action_instances = relationship('ActionInstance', backref="workflow_instance", order_by="asc(ActionInstance.order)")
