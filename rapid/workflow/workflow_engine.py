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
# pylint: disable=too-many-instance-attributes
import datetime
import logging

from rapid.lib.store_service import StoreService
from rapid.lib.constants import StatusTypes, status_type_severity_mapping, StatusConstants
from rapid.workflow.data.dal.status_dal import StatusDal
from rapid.workflow.data.models import Pipeline, PipelineInstance, Stage, StageInstance, Action, \
    ActionInstance, Workflow, WorkflowInstance
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

    def _get_action(self, _id):
        self._load_pipeline()
        return self.action_mapper[_id]

    def _get_workflow(self, _id):
        self._load_pipeline()
        return self.workflow_mapper[_id]

    def _get_stage(self, _id):
        self._load_pipeline()
        return self.stage_mapper[_id]


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
        pipeline_id = self.pipeline.id
        StoreService.set_calculating_workflow(pipeline_id)

        try:
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
                status = StatusConstants.FAILED if status_id != StatusConstants.CANCELED else StatusConstants.CANCELED

                self.complete_a_workflow(action_instance.workflow_instance_id, status)
        finally:
            StoreService.clear_calculating_workflow(pipeline_id)

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

        if self._reconciled_stages(self._load_pipeline(), stage_instance):
            all_complete, all_passed, failed_type = self._check_and_verify_statuses(self._get_stages(self.pipeline))

            if all_complete:
                self.complete_a_pipeline(StatusConstants.SUCCESS if all_passed else failed_type.id)

    def complete_a_pipeline(self, status_id):
        pipeline_instance = self._load_pipeline()
        self._mark_pipeline_instance_complete(pipeline_instance, status_id)

    def _reconciled_stages(self, pipeline_instance, stage_instance):
        if StatusConstants.SUCCESS == stage_instance.status_id and len(self._get_stages(pipeline_instance)) < len(pipeline_instance.pipeline.stages):
            _next = False
            for stage in pipeline_instance.pipeline.stages:
                if stage.id == stage_instance.stage_id:
                    _next = True
                elif _next:
                    new_instance = stage.convert_to_instance()
                    new_instance.start_date = datetime.datetime.utcnow()
                    new_instance.status_id = StatusConstants.INPROGRESS
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
        if StatusConstants.SUCCESS == stage_instance.status_id:
            found = False
            for s_instance in self._get_stages(pipeline_instance):
                if found:
                    s_instance.start_date = datetime.datetime.utcnow()
                    s_instance.status_id = StatusConstants.INPROGRESS

                    for w_instance in self._get_workflows(s_instance):
                        w_instance.start_date = datetime.datetime.utcnow()
                        w_instance.status_id = StatusConstants.INPROGRESS

                        first_order = -1
                        for action in self._get_actions(w_instance):
                            if first_order < 0 or first_order == action.order:
                                action.status_id = StatusConstants.READY
                                first_order = action.order
                    break
                if s_instance.id == stage_instance.id:
                    found = True
            return found
        return True

    def _create_action_instances(self, pipeline_instance, w_instance, workflow):
        first = True
        for action in workflow.actions:
            slices = action.slices
            if slices > 0:
                for _slice in range(1, slices + 1):
                    a_instance = action.convert_to_instance()
                    a_instance.status_id = StatusConstants.READY if first else StatusConstants.NEW
                    a_instance.pipeline_instance_id = pipeline_instance.id
                    a_instance.slice = "{}/{}".format(_slice, action.slices)
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

        return highest_severity < status_type_severity_mapping[StatusTypes.CANCELED]

    def _activate_next_action_all_complete(self, action_instances):
        order_check = None
        all_complete = True
        fail_found = False
        for instance in action_instances:
            if instance.status_id != StatusConstants.NEW:
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

    def reset_pipeline(self):
        now = datetime.datetime.utcnow()
        self.pipeline.status_id = StatusConstants.INPROGRESS
        self.pipeline.start_date = now
        self.pipeline.end_date = None

        first_stage = True
        for stage in self._get_stages(self.pipeline):
            self.reset_stage(stage, first_stage, now)
            first_stage = False

    def reset_stage(self, stage, first_stage=False, now=None):
        now = datetime.datetime.utcnow() if now is None else now

        stage.status_id = StatusConstants.READY if first_stage else StatusConstants.NEW
        stage.created_date = now
        stage.start_date = now if first_stage else None
        stage.end_date = None

        for workflow in self._get_workflows(stage):
            self.reset_workflow(workflow, first_stage, now)

    def reset_workflow(self, workflow, first_stage=False, now=None):
        now = datetime.datetime.utcnow() if now is None else now

        workflow.status_id = StatusConstants.INPROGRESS if first_stage else StatusConstants.NEW
        workflow.start_date = now if first_stage else None
        workflow.end_date = None

        actions = self._get_actions(workflow)
        self.reset_action_instances(actions[0], actions, first_stage)

    def get_action_instance_by_id(self, action_id):
        for stage in self._get_stages(self.pipeline):
            for workflow in self._get_workflows(stage):
                for action in self._get_actions(workflow):
                    if action.id == action_id:
                        return action
        return None

    def reset_action(self, action, first_stage=False):
        action.workflow_instance.status_id = StatusConstants.INPROGRESS if first_stage else StatusConstants.NEW
        action.workflow_instance.end_date = None
        action.workflow_instance.stage_instance.status_id = StatusConstants.INPROGRESS if first_stage else StatusConstants.NEW
        action.workflow_instance.stage_instance.end_date = None

        self.reset_action_instances(action, action.workflow_instance.action_instances, first_stage, single_instance=True)

    def reset_action_instances(self, action_instance, action_instances, first_stage=False, single_instance=False):
        first = True
        first_order = None
        action_order = action_instance.order
        for instance in action_instances:
            current_order = instance.order
            if first_order is None:
                first_order = current_order

            if first and first_order != current_order:
                first = False

            if single_instance:
                if current_order < action_order or action_instance.id == instance.id:
                    if action_instance.id == instance.id:
                        if single_instance:
                            instance.workflow_instance.status_id = StatusConstants.INPROGRESS if not first_stage else StatusConstants.NEW
                            instance.workflow_instance.end_date = None
                            instance.workflow_instance.stage_instance.end_date = None
                            instance.workflow_instance.stage_instance.status_id = StatusConstants.INPROGRESS if not first_stage else StatusConstants.NEW
                            self.pipeline.end_date = None
                            self.pipeline.status_id = StatusConstants.INPROGRESS

                    instance.status_id = StatusConstants.NEW if not first else StatusConstants.READY
                    instance.start_date = None
                    instance.assigned_to = None
                    instance.end_date = None
                elif instance.order == current_order:
                    continue
                else:
                    break
            else:
                instance.status_id = StatusConstants.NEW if not (first and first_stage) else StatusConstants.READY
                instance.start_date = None
                instance.assigned_to = None
                instance.end_date = None


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
