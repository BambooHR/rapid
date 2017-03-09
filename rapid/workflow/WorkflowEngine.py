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

from rapid.lib.Constants import StatusTypes, status_type_severity_mapping, StatusConstants
from rapid.workflow.data.dal.StatusDal import StatusDal
from rapid.workflow.data.models import Pipeline, PipelineInstance, Stage, StageInstance, Action, \
    ActionInstance, Workflow, WorkflowInstance

import logging
logger = logging.getLogger('rapid')


class WorkflowEngine(object):
    def __init__(self, pipeline):
        self.pipeline = pipeline

        self.pipeline_class = Pipeline
        self.stage_class = Stage
        self.workflow_class = Workflow
        self.action_class = Action

        self.stage_mapper = {}
        self.workflow_mapper = {}
        self.action_mapper = {}
        self.status_cache = {}
        self.__loaded__ = False

    def _load_pipeline(self):
        if not self.__loaded__:
            for stage in self._get_stages(self.pipeline):
                self.stage_mapper[stage.id] = stage
                for workflow in self._get_workflows(stage):
                    self.workflow_mapper[workflow.id] = workflow
                    for action in self._get_actions(workflow):
                        self.action_mapper[action.id] = action
            self.__loaded__ = True
        return self.pipeline

    def _get_stages(self, pipeline):
        return pipeline.stages

    def _get_workflows(self, stage):
        return stage.workflows

    def _get_workflows_by_stage_id(self, stage_id):
        return self._get_workflows(self._get_stage(stage_id))

    def _get_actions(self, workflow):
        return workflow.actions

    def _get_actions_by_workflow_id(self, workflow_id):
        return self._get_actions(self._get_workflow(workflow_id))

    def _get_action(self, id):
        self._load_pipeline()
        return self.action_mapper[id]

    def _get_workflow(self, id):
        self._load_pipeline()
        return self.workflow_mapper[id]

    def _get_stage(self, id):
        self._load_pipeline()
        return self.stage_mapper[id]


class InstanceWorkflowEngine(WorkflowEngine):
    __injectables__ = {'status_dal': StatusDal}

    def __init__(self, status_dal, pipeline_instance):
        super(InstanceWorkflowEngine, self).__init__(pipeline_instance)
        self.status_dal = status_dal

        self.pipeline_class = PipelineInstance
        self.stage_class = StageInstance
        self.workflow_class = WorkflowInstance
        self.action_class = ActionInstance
        self.instances_to_add = []

    def _get_stages(self, pipeline):
        return pipeline.stage_instances

    def _get_workflows(self, stage):
        return stage.workflow_instances

    def _get_actions(self, workflow):
        return workflow.action_instances

    def complete_an_action(self, action_instance_id, status_id):
        """
        1. Load all the action_instances
        1a. Set status
        2. If status is "successful"
        2a. If sliced, check all others if done. If last move to 3.
        3. If last in workflow, record date end with workflow, status to highest severity
        4. If successful workflow, check all other workflows. If done, set status and date for stage.
        5. Create new stageInstance if another exists.
        6. If last stage, complete the Pipeline Instance
        :param status_id:
        :param action_instance_id:
        """
        action_instance = self._get_action(action_instance_id)
        self._mark_action_instance_complete(action_instance, status_id)

        action_instances = self._get_actions_by_workflow_id(action_instance.workflow_instance_id)
        if self._can_continue_workflow(action_instances):
            if self._activate_next_action_all_complete(action_instances):
                self.complete_a_workflow(action_instance.workflow_instance_id, StatusConstants.SUCCESS)
        else:
            for instance in action_instances:
                if instance.status_id == StatusConstants.NEW:
                    self._mark_action_instance_complete(instance, StatusConstants.CANCELED)
            self.complete_a_workflow(action_instance.workflow_instance_id, StatusConstants.FAILED)

    def complete_a_workflow(self, workflow_instance_id, status_id):
        workflow_instance = self._get_workflow(workflow_instance_id)
        self._mark_workflow_instance_complete(workflow_instance, status_id)

        # Are all the other workflows complete?
        all_complete, all_passed, failed_type = self._check_and_verify_statuses(self._get_workflows_by_stage_id(workflow_instance.stage_instance_id))

        if all_complete:
            self.complete_a_stage(workflow_instance.stage_instance_id,
                                  StatusConstants.SUCCESS if all_passed else failed_type.id)

    def complete_a_stage(self, stage_instance_id, status_id):
        stage_instance = self._get_stage(stage_instance_id)
        self._mark_stage_instance_complete(stage_instance, status_id)

        if self._reconciled_stages(self.pipeline, stage_instance):
            all_complete, all_passed, failed_type = self._check_and_verify_statuses(self._get_stages(self.pipeline))

            if all_complete:
                self.complete_a_pipeline(self.pipeline.id, StatusConstants.SUCCESS if all_passed else failed_type.id)

    def complete_a_pipeline(self, pipeline_instance_id, status_id):
        pipeline_instance = self._load_pipeline()
        self._mark_pipeline_instance_complete(pipeline_instance, status_id)

    def _reconciled_stages(self, pipeline_instance, stage_instance):
        if StatusConstants.SUCCESS == stage_instance.status_id and len(self._get_stages(pipeline_instance)) < len(pipeline_instance.pipeline.stages):
            next = False
            for stage in pipeline_instance.pipeline.stages:
                if stage.id == stage_instance.stage_id:
                    next = True
                elif next:
                    new_instance = stage.convert_to_instance()
                    new_instance.start_date = datetime.datetime.utcnow()
                    new_instance.pipeline_instance_id = pipeline_instance.id
                    for workflow in stage.workflows:
                        w_instance = workflow.convert_to_instance()
                        w_instance.start_date = datetime.datetime.utcnow()
                        self._create_action_instances(pipeline_instance, w_instance, workflow)
                        new_instance.workflow_instances.append(w_instance)
                        self.instances_to_add.append(w_instance)
                    self.instances_to_add.append(new_instance)
                    break
            return False
        return True

    def _create_action_instances(self, pipeline_instance, w_instance, workflow):
        first = True
        for action in workflow.actions:
            slices = action.slices
            if slices > 0:
                for slice in range(1, slices + 1):
                    a_instance = action.convert_to_instance()
                    a_instance.status_id = StatusConstants.READY if first else StatusConstants.NEW
                    a_instance.pipeline_instance_id = pipeline_instance.id
                    a_instance.slice = "{}/{}".format(slice, action.slices)
                    w_instance.action_instances.append(a_instance)
                    self.instances_to_add.append(a_instance)
                first = False
            else:
                a_instance = action.convert_to_instance()
                a_instance.status_id = StatusConstants.READY if first else StatusConstants.NEW
                a_instance.pipeline_instance_id = pipeline_instance.id
                a_instance.slice = "1/1"
                first = False
                w_instance.action_instances.append(a_instance)
                self.instances_to_add.append(a_instance)

    def _check_and_verify_statuses(self, objects):
        all_complete = True
        all_passed = True
        failed_type = None

        for instance in objects:
            if instance.status_id <= StatusConstants.INPROGRESS:
                all_complete = False
                break

            status = self._get_status(instance.status_id)
            if status.type == StatusTypes.FAILED or status.type == StatusTypes.CANCELED:
                all_passed = False
                failed_type = status

        return all_complete, all_passed, failed_type

    def _get_status(self, status_id):
        if status_id not in self.status_cache:
            self.status_cache[status_id] = self.status_dal.get_status_by_id(status_id)
        return self.status_cache[status_id]

    def _can_continue_workflow(self, actions):
        """
        :param actions:
        :type actions: list[ActionInstance]
        :return:
        :rtype:
        """
        highest_severity = -1
        sliced_statuses = []
        current_action_id = None
        for instance in actions:
            if current_action_id is None:
                current_action_id = instance.action_id
                sliced_statuses.append(int(instance.status_id))
            elif current_action_id == instance.action_id:
                sliced_statuses.append(int(instance.status_id))
            else:
                current_action_id = instance.action_id

            if instance.status_id >= StatusConstants.INPROGRESS:
                status = self._get_status(instance.status_id)

                if status.type in status_type_severity_mapping:
                    severity = status_type_severity_mapping[status.type]
                    highest_severity = max(severity, highest_severity)
        if StatusConstants.NEW in sliced_statuses \
                or StatusConstants.READY in sliced_statuses \
                or StatusConstants.INPROGRESS in sliced_statuses:
            return True
        else:
            return highest_severity < status_type_severity_mapping[StatusTypes.FAILED]

    def _activate_next_action_all_complete(self, action_instances):
        order_check = None
        all_complete = True
        fail_found = False
        for instance in action_instances:
            if instance.status_id != StatusConstants.NEW:
                status = self._get_status(instance.status_id)
                if instance.status_id == StatusConstants.INPROGRESS:
                    all_complete = False
                    break  # if you are inprogress, don't bother checking the rest.
                elif instance.status_id == StatusConstants.READY:
                    all_complete = False
                elif instance.status_id > StatusConstants.SUCCESS:
                    fail_found = True
                order_check = instance.order
                continue

            if fail_found:
                break

            if order_check is None or order_check == instance.order:
                instance.status_id = StatusConstants.READY
                order_check = instance.order
                all_complete = False
            if all_complete and order_check < instance.order:
                instance.status_id = StatusConstants.READY
                all_complete = False
                order_check = instance.order
                # break
        return all_complete

    @staticmethod
    def _mark_action_instance_complete(action_instance, status_id):
        action_instance.status_id = status_id
        action_instance.end_date = datetime.datetime.utcnow() if status_id != StatusConstants.CANCELED else action_instance.start_date

    @staticmethod
    def _mark_workflow_instance_complete(workflow_instance, status_id):
        workflow_instance.status_id = status_id
        workflow_instance.end_date = datetime.datetime.utcnow()

    @staticmethod
    def _mark_stage_instance_complete(stage_instance, status_id):
        stage_instance.status_id = status_id
        stage_instance.end_date = datetime.datetime.utcnow() if status_id != StatusConstants.CANCELED else stage_instance.start_date

    @staticmethod
    def _mark_pipeline_instance_complete(pipeline_instance, status_id):
        pipeline_instance.status_id = status_id
        pipeline_instance.end_date = datetime.datetime.utcnow()
