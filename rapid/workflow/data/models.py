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
# pylint: disable=no-member,too-few-public-methods,broad-except
import datetime

from sqlalchemy.orm import relationship
from sqlalchemy import Column, String, ForeignKey, Integer, Boolean, Text, desc, DateTime

from rapid.lib import get_declarative_base
from rapid.lib.constants import StatusConstants
from rapid.lib.converters import ObjectConverter
from rapid.master.data.database.models.base.base_model import BaseModel
from rapid.master.data.database.models.base.date_model import DateModel
from rapid.master.data.database.models.base.active_model import ActiveModel
Base = get_declarative_base()


class Action(BaseModel, Base):
    cmd = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    executable = Column(String(100), nullable=False)
    args = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False, index=True)
    manual = Column(Boolean, default=False, nullable=False)
    callback_required = Column(Boolean, default=False, nullable=False)
    grain = Column(String(100))
    slices = Column(Integer, default=0)

    workflow_id = Column(Integer, ForeignKey('workflows.id'), nullable=False, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False, index=True)

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


class ActionInstance(DateModel, BaseModel, Base):
    cmd = Column(String(255), nullable=False)
    executable = Column(String(100), nullable=False)
    args = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False, default=0, index=True)
    manual = Column(Boolean, nullable=False, default=False)
    callback_required = Column(Boolean, nullable=False, default=False)
    grain = Column(String(100))
    assigned_to = Column(String(75), nullable=True)
    slice = Column(String(25), default='')

    status_id = Column(Integer, ForeignKey('statuses.id'), nullable=False, index=True)
    action_id = Column(Integer, ForeignKey('actions.id'), nullable=False, index=True)

    workflow_instance_id = Column(Integer, ForeignKey('workflow_instances.id'), nullable=False, index=True)
    pipeline_instance_id = Column(Integer, ForeignKey("pipeline_instances.id"), nullable=False, index=True)

    status = relationship('Status')
    pipeline_instance = relationship('PipelineInstance')
    action = relationship('Action')


class IntegrationType(BaseModel, Base):
    name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True, nullable=False)


class IntegrationKeys(BaseModel, Base):
    name = Column(String(255), nullable=False)
    active = Column(Boolean, default=True, nullable=False)


class Integration(BaseModel, Base):
    integration_type_id = Column(Integer, ForeignKey('integration_types.id'), nullable=False)
    integration_keys_id = Column(Integer, ForeignKey('integration_keys.id'), nullable=False)
    value = Column(String(500), nullable=False)


class Pipeline(ActiveModel, Base):
    stages = relationship("Stage", backref="pipeline", order_by="asc(Stage.order)")

    pipeline_events = relationship('PipelineEvent', backref="pipeline")

    def convert_to_instance(self):
        instance = PipelineInstance()
        instance.pipeline_id = self.id                                                                                                                                   
        return ObjectConverter.copy_attributes(self, instance, [])


class PipelineInstance(BaseModel, DateModel, Base):
    pipeline_id = Column(Integer, ForeignKey('pipelines.id'), nullable=False, index=True)
    status_id = Column(Integer, ForeignKey('statuses.id'), nullable=False, index=True)
    priority = Column(Integer, default=0, index=True)

    stage_instances = relationship("StageInstance", backref="pipeline_instance", order_by="asc(StageInstance.order)")
    action_instances = relationship("ActionInstance", order_by="ActionInstance.id")
    parameters = relationship('PipelineParameters', backref="pipeline_instance")
    stats = relationship('PipelineStatistics', backref="pipeline_instance")
    pipeline = relationship('Pipeline')
    status = relationship('Status')

    def get_parameters_dict(self):
        results = {}
        try:
            for parameter in self.parameters:
                results[parameter.parameter] = parameter.value

            results['pipeline_instance_id'] = self.id
        except Exception:
            pass
        return results


class PipelineParameters(BaseModel, Base):
    pipeline_instance_id = Column(Integer, ForeignKey("pipeline_instances.id"), nullable=False, index=True)
    parameter = Column(String(200), nullable=False, index=True)
    value = Column(String(4000), nullable=False)


class PipelineStatistics(BaseModel, Base):
    pipeline_instance_id = Column(Integer, ForeignKey("pipeline_instances.id"), nullable=False, index=True)
    statistics_id = Column(Integer, ForeignKey("statistics.id"), nullable=False, index=True)
    value = Column(Integer, nullable=False)

    statistics = relationship('Statistics', backref="pipeline_statistics")


class Stage(ActiveModel, Base):
    order = Column(Integer, nullable=False, default=0, index=True)
    pipeline_id = Column(Integer, ForeignKey("pipelines.id"), nullable=False, index=True)

    workflows = relationship("Workflow", backref="stage")

    def convert_to_instance(self):
        instance = StageInstance()
        instance.status_id = StatusConstants.NEW
        instance.stage_id = self.id
        instance.start_date = datetime.datetime.utcnow()
        return ObjectConverter.copy_attributes(self, instance, ['order'])


class StageInstance(BaseModel, DateModel, Base):
    order = Column(Integer, nullable=False, default=0, index=True)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False, index=True)
    pipeline_instance_id = Column(Integer, ForeignKey("pipeline_instances.id"), nullable=False, index=True)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=False, index=True)

    stage = relationship('Stage')
    status = relationship('Status')

    workflow_instances = relationship("WorkflowInstance", backref="stage_instance", order_by="asc(WorkflowInstance.order)")


class Statistics(ActiveModel, Base):
    pass


class Status(ActiveModel, Base):
    type = Column(String(50), nullable=False, index=True)
    display_name = Column(String(100), nullable=False)


class Workflow(ActiveModel, Base):
    order = Column(Integer, nullable=False, default=0, index=True)
    stage_id = Column(Integer, ForeignKey("stages.id"), nullable=False, index=True)

    actions = relationship("Action", backref="workflow", order_by="asc(Action.order)")

    def convert_to_instance(self):
        instance = WorkflowInstance()
        instance.status_id = StatusConstants.NEW
        instance.workflow_id = self.id
        instance.start_date = datetime.datetime.utcnow()
        return ObjectConverter.copy_attributes(self, instance, ['order'])


class WorkflowInstance(BaseModel, DateModel, Base):
    order = Column(Integer, nullable=False, default=0, index=True)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False, index=True)
    stage_instance_id = Column(Integer, ForeignKey("stage_instances.id"), nullable=False, index=True)
    workflow_id = Column(Integer, ForeignKey('workflows.id'), nullable=False, index=True)

    status = relationship('Status')
    workflow = relationship('Workflow')
    action_instances = relationship('ActionInstance', backref="workflow_instance", order_by="asc(ActionInstance.order)")


class EventType(ActiveModel, Base):
    pass


class PipelineEvent(BaseModel, Base):
    pipeline_id = Column(ForeignKey('pipelines.id'), nullable=False, index=True)
    event_type_id = Column(ForeignKey('event_types.id'), nullable=False, index=True)
    conditional = Column(Text, nullable=False)
    config = Column(Text, nullable=False)


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
