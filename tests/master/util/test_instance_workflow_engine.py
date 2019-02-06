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
from unittest.case import TestCase

from mock.mock import Mock
from nose.tools.trivial import eq_, ok_

from rapid.lib.constants import StatusConstants, StatusTypes
from rapid.workflow.workflow_engine import InstanceWorkflowEngine
from rapid.workflow.data.models import PipelineInstance, StageInstance, WorkflowInstance, ActionInstance, \
    Status, Pipeline, Stage, Workflow, Action


class TestInstanceWorkflowEngine(TestCase):

    def test_init(self):
        status_dal = Mock()
        pipeline_instance = PipelineInstance(id=1)
        workflow_engine = InstanceWorkflowEngine(status_dal, pipeline_instance)

        eq_(workflow_engine.pipeline, pipeline_instance)
        eq_(status_dal, workflow_engine.status_dal)
        eq_(PipelineInstance, workflow_engine.pipeline_class)
        eq_(StageInstance, workflow_engine.stage_class)
        eq_(WorkflowInstance, workflow_engine.workflow_class)
        eq_(ActionInstance, workflow_engine.action_class)

    def test_get_stages(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        stage_instance = StageInstance()
        pipeline_instance = PipelineInstance(stage_instances=[stage_instance])
        eq_([stage_instance], workflow_engine._get_stages(pipeline_instance))

    def test_get_workflows(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        workflow_instance = WorkflowInstance()
        stage_instance = StageInstance(workflow_instances=[workflow_instance])
        eq_([workflow_instance], workflow_engine._get_workflows(stage_instance))

    def test_get_actions(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        action_instance = ActionInstance()
        workflow_instance = WorkflowInstance(action_instances=[action_instance])
        eq_([action_instance], workflow_engine._get_actions(workflow_instance))

    # Test the complete code

    # Test the helper methods
    def test_get_status(self):
        status_dal = Mock()
        status = Status(id=1, name="Something")
        status_dal.get_status_by_id.return_value = status

        workflow_engine = InstanceWorkflowEngine(status_dal, Mock())

        eq_(status, workflow_engine._get_status(1))
        eq_({1: status}, workflow_engine.status_cache)

    def test_check_verify_statuses_simple(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())

        all_complete, all_passed, failed_type = workflow_engine._check_and_verify_statuses([StageInstance(status_id=StatusConstants.NEW)])
        eq_(False, all_complete)
        eq_(True, all_passed)
        eq_(None, failed_type)

    def test_check_verify_statuses_simple_inprogress(self):
        self._testing_check_verify([StageInstance(status_id=StatusConstants.INPROGRESS)], [False, True, None])

    def test_check_verify_status_complex_all_pass(self):
        self._testing_check_verify([ActionInstance(status_id=StatusConstants.SUCCESS),
                                    ActionInstance(status_id=StatusConstants.SUCCESS),
                                    ActionInstance(status_id=StatusConstants.INPROGRESS),
                                    ActionInstance(status_id=StatusConstants.NEW)],
                                   [False, True, None])

    def test_check_verify_status_complex_one_canceled(self):
        self._testing_check_verify([ActionInstance(status_id=StatusConstants.SUCCESS),
                                    ActionInstance(status_id=StatusConstants.CANCELED)],
                                   [True, False, Status(id=StatusConstants.CANCELED, type=StatusTypes.CANCELED, name="Testing CANCELED")])

    def test_check_verify_status_complex_one_failed(self):
        self._testing_check_verify([ActionInstance(status_id=StatusConstants.SUCCESS),
                                    ActionInstance(status_id=StatusConstants.FAILED),
                                    ActionInstance(status_id=StatusConstants.NEW)],
                                   [False, False, Status(id=StatusConstants.FAILED, type=StatusTypes.FAILED, name="Testing FAILED")])

    # Test mark methods
    def test_mark_action_instance_complete(self):
        action_instance = ActionInstance()
        InstanceWorkflowEngine._mark_action_instance_complete(action_instance, StatusConstants.SUCCESS)

        eq_(StatusConstants.SUCCESS, action_instance.status_id)
        ok_(action_instance.end_date is not None)

    def test_mark_action_instance_complete_canceled(self):
        action_instance = ActionInstance(start_date=datetime.datetime.utcnow())
        InstanceWorkflowEngine._mark_action_instance_complete(action_instance, StatusConstants.CANCELED)

        eq_(action_instance.start_date, action_instance.end_date)

    def test_mark_workflow_instance_complete(self):
        workflow_instance = WorkflowInstance()
        InstanceWorkflowEngine._mark_workflow_instance_complete(workflow_instance, StatusConstants.FAILED)

        eq_(StatusConstants.FAILED, workflow_instance.status_id)
        ok_(workflow_instance.end_date is not None)

    def test_mark_stage_instance_complete(self):
        stage_instance = StageInstance()
        InstanceWorkflowEngine._mark_stage_instance_complete(stage_instance, StatusConstants.SUCCESS)

        eq_(StatusConstants.SUCCESS, stage_instance.status_id)
        ok_(stage_instance.end_date is not None)

    def test_mark_stage_instance_complete_canceled(self):
        stage_instance = StageInstance(start_date=datetime.datetime.utcnow())
        InstanceWorkflowEngine._mark_stage_instance_complete(stage_instance, StatusConstants.CANCELED)

        eq_(stage_instance.start_date, stage_instance.end_date)

    def test_mark_pipeline_instance_complete(self):
        pipeline_instance = PipelineInstance()
        InstanceWorkflowEngine._mark_pipeline_instance_complete(pipeline_instance, StatusConstants.FAILED)

        eq_(StatusConstants.FAILED, pipeline_instance.status_id)
        ok_(pipeline_instance.end_date is not None)

    def test_reconciled_stages(self):
        stage_instance = StageInstance(id=2, status_id=StatusConstants.SUCCESS, stage_id=2)
        pipeline_instance = PipelineInstance(stage_instances=[StageInstance(id=1, status_id=StatusConstants.SUCCESS), stage_instance],
                                             pipeline=Pipeline(stages=[Stage(id=1), Stage(id=2)]))
        instance_workflow_engine = InstanceWorkflowEngine(Mock(), pipeline_instance)
        instance_workflow_engine._load_pipeline()
        instance_workflow_engine.complete_a_stage(2, StatusConstants.SUCCESS)

        eq_(StatusConstants.SUCCESS, pipeline_instance.status_id)
        ok_(pipeline_instance.end_date is not None)

    def test_can_continue_workflow_status_not_in_severity(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        workflow_engine.status_cache[StatusConstants.SUCCESS] = Status(id=StatusConstants.SUCCESS, type=StatusTypes.SUCCESS)
        workflow_engine.status_cache[100] = Status(id=100, type="semiborked")

        ok_(workflow_engine._can_continue_workflow([ActionInstance(status_id=100), ActionInstance(status_id=StatusConstants.SUCCESS)]))

    def test_can_continue_workflow_should_fail(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        workflow_engine.status_cache[StatusConstants.SUCCESS] = Status(id=StatusConstants.SUCCESS, type=StatusTypes.SUCCESS)
        workflow_engine.status_cache[100] = Status(id=100, type=StatusTypes.FAILED)

        ok_(not workflow_engine._can_continue_workflow([ActionInstance(status_id=100), ActionInstance(status_id=StatusConstants.SUCCESS)]))

    def test_can_continue_workflow_should_continue_with_sliced_actions(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        workflow_engine.status_cache[StatusConstants.SUCCESS] = Status(id=StatusConstants.READY, type=StatusTypes.SUCCESS)
        workflow_engine.status_cache[100] = Status(id=100, type=StatusTypes.FAILED)

        ok_(workflow_engine._can_continue_workflow([ActionInstance(status_id=100, slice='1/2', action_id=1), ActionInstance(status_id=StatusConstants.READY, slice='1/1', action_id=1)]))

    def test_activate_next_action_all_complete_simple(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        action_instances = [ActionInstance(status_id=StatusConstants.NEW)]
        workflow_engine._activate_next_action_all_complete(action_instances)

        eq_(StatusConstants.READY, action_instances[0].status_id)

    def test_activate_next_action_all_complete_with_ready(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        action_instances = [ActionInstance(status_id=StatusConstants.SUCCESS, order=0),
                            ActionInstance(status_id=StatusConstants.READY, order=1),
                            ActionInstance(status_id=StatusConstants.NEW, order=2)]
        workflow_engine._activate_next_action_all_complete(action_instances)

        eq_(StatusConstants.READY, action_instances[1].status_id)
        eq_(StatusConstants.NEW, action_instances[2].status_id)

    def test_activate_next_action_all_complete_with_orders(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        action_instances = [ActionInstance(status_id=StatusConstants.SUCCESS, order=0),
                            ActionInstance(status_id=StatusConstants.NEW, order=1),
                            ActionInstance(status_id=StatusConstants.NEW, order=2)]
        workflow_engine._activate_next_action_all_complete(action_instances)

        eq_(StatusConstants.READY, action_instances[1].status_id)
        eq_(StatusConstants.NEW, action_instances[2].status_id)

    def test_activate_next_action_all_complete_with_same_order(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        action_instances = [ActionInstance(status_id=StatusConstants.SUCCESS, order=0),
                            ActionInstance(status_id=StatusConstants.READY, order=1),
                            ActionInstance(status_id=StatusConstants.NEW, order=1)]
        workflow_engine._activate_next_action_all_complete(action_instances)

        eq_(StatusConstants.READY, action_instances[1].status_id)
        eq_(StatusConstants.READY, action_instances[2].status_id)

    def test_activate_next_action_all_complete_with_same_order_multiple_new(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        action_instances = [ActionInstance(status_id=StatusConstants.SUCCESS, order=0),
                            ActionInstance(status_id=StatusConstants.NEW, order=1),
                            ActionInstance(status_id=StatusConstants.NEW, order=1),
                            ActionInstance(status_id=StatusConstants.NEW, order=2)]
        return_value = workflow_engine._activate_next_action_all_complete(action_instances)

        eq_(StatusConstants.READY, action_instances[1].status_id)
        eq_(StatusConstants.READY, action_instances[2].status_id)
        eq_(StatusConstants.NEW, action_instances[3].status_id)
        ok_(not return_value)

    def test_activate_next_action_all_complete_with_inprogress(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        action_instances = [ActionInstance(status_id=StatusConstants.SUCCESS, order=0),
                            ActionInstance(status_id=StatusConstants.INPROGRESS, order=1),
                            ActionInstance(status_id=StatusConstants.NEW, order=2)]
        workflow_engine._activate_next_action_all_complete(action_instances)

        eq_(StatusConstants.INPROGRESS, action_instances[1].status_id)
        eq_(StatusConstants.NEW, action_instances[2].status_id)

    def test_activate_next_action_all_complete_with_failed(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        workflow_engine.status_cache[StatusConstants.FAILED] = Status(type=StatusTypes.FAILED)

        action_instances = [ActionInstance(status_id=StatusConstants.SUCCESS, order=0),
                            ActionInstance(status_id=StatusConstants.FAILED, order=1),
                            ActionInstance(status_id=StatusConstants.NEW, order=2)]
        workflow_engine._activate_next_action_all_complete(action_instances)

        eq_(StatusConstants.FAILED, action_instances[1].status_id)
        eq_(StatusConstants.NEW, action_instances[2].status_id)

    def test_activate_next_action_all_complete_with_canceled(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        workflow_engine.status_cache[StatusConstants.CANCELED] = Status(type=StatusTypes.CANCELED)

        action_instances = [ActionInstance(status_id=StatusConstants.SUCCESS, order=0),
                            ActionInstance(status_id=StatusConstants.CANCELED, order=1),
                            ActionInstance(status_id=StatusConstants.NEW, order=2)]
        workflow_engine._activate_next_action_all_complete(action_instances)

        eq_(StatusConstants.CANCELED, action_instances[1].status_id)
        eq_(StatusConstants.NEW, action_instances[2].status_id)

    def test_activate_next_action_all_complete_with_unknown(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        workflow_engine.status_cache[StatusConstants.UNKNOWN] = Status(type=StatusTypes.WARNING)

        action_instances = [ActionInstance(status_id=StatusConstants.SUCCESS, order=0),
                            ActionInstance(status_id=StatusConstants.UNKNOWN, order=1),
                            ActionInstance(status_id=StatusConstants.NEW, order=2)]
        workflow_engine._activate_next_action_all_complete(action_instances)

        eq_(StatusConstants.UNKNOWN, action_instances[1].status_id)
        eq_(StatusConstants.NEW, action_instances[2].status_id)

    def test_create_action_instance_with_no_slicing(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())

        workflow_instance = WorkflowInstance(id=1)
        workflow = Workflow(actions=[Action(slices=0, id=1, cmd="test1"), Action(slices=0, id=2, cmd="test2")])
        workflow_engine._create_action_instances(Mock(id=1), workflow_instance, workflow)

        eq_(2, len(workflow_instance.action_instances))
        eq_('test1', workflow_instance.action_instances[0].cmd)
        eq_(StatusConstants.READY, workflow_instance.action_instances[0].status_id)
        eq_('test2', workflow_instance.action_instances[1].cmd)
        eq_(StatusConstants.NEW, workflow_instance.action_instances[1].status_id)

    def test_create_action_instance_with_slicing_after(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())

        workflow_instance = WorkflowInstance(id=1)
        workflow = Workflow(actions=[Action(slices=0, id=1, cmd="test1"), Action(slices=4, id=2, cmd="test2")])
        workflow_engine._create_action_instances(Mock(id=1), workflow_instance, workflow)

        eq_(5, len(workflow_instance.action_instances))
        eq_('test1', workflow_instance.action_instances[0].cmd)
        eq_(StatusConstants.READY, workflow_instance.action_instances[0].status_id)
        for i in range(1, 5):
            eq_('test2', workflow_instance.action_instances[i].cmd)
            eq_(StatusConstants.NEW, workflow_instance.action_instances[i].status_id)

    def test_create_action_instance_with_slicing_before(self):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())

        workflow_instance = WorkflowInstance(id=1)
        workflow = Workflow(actions=[Action(slices=4, id=1, cmd="test1"), Action(slices=0, id=2, cmd="test2")])
        workflow_engine._create_action_instances(Mock(id=1), workflow_instance, workflow)

        eq_(5, len(workflow_instance.action_instances))
        for i in range(0, 4):
            eq_('test1', workflow_instance.action_instances[i].cmd)
            eq_(StatusConstants.READY, workflow_instance.action_instances[i].status_id)

        eq_('test2', workflow_instance.action_instances[4].cmd)
        eq_(StatusConstants.NEW, workflow_instance.action_instances[4].status_id)

    def test_reset_pipeline_instance_status_set_to_inprogress(self):
        pipeline_instance = self._build_pipeline_instance(['1:1', '7:1-1-1-1,1,4,1-1-1-1'])

        workflow_engine = InstanceWorkflowEngine(self._get_mocked_dal(), pipeline_instance)
        workflow_engine.reset_pipeline()
        self.assertEqual(StatusConstants.INPROGRESS, pipeline_instance.status_id)

    def test_reset_pipeline_instance_first_action_instance_and_orders_are_set_to_inprogress(self):
        pipeline_instance = self._build_pipeline_instance(['2:1-2,1'])

        workflow_engine = InstanceWorkflowEngine(self._get_mocked_dal(), pipeline_instance)
        workflow_engine.reset_pipeline()
        self.assertEqual(StatusConstants.READY, pipeline_instance.stage_instances[0].workflow_instances[0].action_instances[0].status_id)
        self.assertEqual(StatusConstants.READY, pipeline_instance.stage_instances[0].workflow_instances[1].action_instances[0].status_id)
        self.assertEqual(StatusConstants.READY, pipeline_instance.stage_instances[0].workflow_instances[1].action_instances[1].status_id)
        self.assertEqual(StatusConstants.NEW, pipeline_instance.stage_instances[0].workflow_instances[1].action_instances[2].status_id)

    def test_reset_pipeline_instance_sets_appropriate_dates(self):
        pipeline_instance = self._build_pipeline_instance(['1:1', '1:1'])
        pipeline_instance.end_date = datetime.datetime.utcnow()

        workflow_engine = InstanceWorkflowEngine(self._get_mocked_dal(), pipeline_instance)
        workflow_engine.reset_pipeline()
        self.assertTrue(pipeline_instance.start_date is not None, "Start date was not set.")
        self.assertTrue(pipeline_instance.end_date is None, 'End date was not reset.')

    def test_reset_action_instance(self):
        pipeline_instance = self._build_pipeline_instance(['1:1', '2:1-2,1'], True)

        workflow_engine = InstanceWorkflowEngine(self._get_mocked_dal(), pipeline_instance)
        action_instance = workflow_engine.get_action_instance_by_id(3)
        workflow_engine.reset_action(action_instance)

        self.assertEquals(None, pipeline_instance.end_date)
        self.assertEquals(None, pipeline_instance.stage_instances[1].end_date)
        self.assertEquals(None, pipeline_instance.stage_instances[1].workflow_instances[1].end_date)
        self.assertEquals(None, action_instance.end_date)
        self.assertEquals(StatusConstants.READY, action_instance.status_id)

    def test_complete_an_action_instance_sets_dates_and_status(self):
        pipeline_instance = self._build_pipeline_instance(['1:1'])

        workflow_engine = InstanceWorkflowEngine(self._get_mocked_dal(), pipeline_instance)
        action_instance = workflow_engine.get_action_instance_by_id(1)
        workflow_engine.complete_an_action(action_instance.id, StatusConstants.CANCELED)

        self.assertEqual(StatusConstants.CANCELED, action_instance.status_id)
        self.assertEqual(StatusConstants.CANCELED, pipeline_instance.status_id)
        self.assertEqual(StatusConstants.CANCELED, pipeline_instance.stage_instances[0].status_id)
        self.assertEqual(StatusConstants.CANCELED, pipeline_instance.stage_instances[0].workflow_instances[0].status_id)

    def test_complete_an_action_instance_starts_next(self):
        pipeline_instance = self._build_pipeline_instance(['1:2'])
        pipeline_instance.status_id = StatusConstants.INPROGRESS
        
        workflow_engine = InstanceWorkflowEngine(self._get_mocked_dal(), pipeline_instance)
        action_instance = workflow_engine.get_action_instance_by_id(2)
        workflow_engine.complete_an_action(1, StatusConstants.SUCCESS)

        self._print_pipeline_instance(pipeline_instance)

        self.assertEqual(StatusConstants.READY, action_instance.status_id)
        self.assertEqual(StatusConstants.INPROGRESS, pipeline_instance.status_id)
        self.assertEqual(StatusConstants.SUCCESS, pipeline_instance.stage_instances[0].workflow_instances[0].action_instances[0].status_id)
        self.assertEqual(StatusConstants.READY, pipeline_instance.stage_instances[0].workflow_instances[0].action_instances[1].status_id)

    @staticmethod
    def _print_pipeline_instance(pipeline_instance):
        print("pipeline: {}, Status: {}, Start Date: {}, End Date:{}".format(pipeline_instance.id, pipeline_instance.status_id, pipeline_instance.start_date, pipeline_instance.end_date))
        for stage_instance in pipeline_instance.stage_instances:
            print("stage: {}, Status: {}, Start Date: {}, End Date: {}".format(stage_instance.id, stage_instance.status_id, stage_instance.start_date, stage_instance.end_date))
            for workflow_instance in stage_instance.workflow_instances:
                print("  workflow: {}, Status: {}, Start Date: {}, End Date: {}".format(workflow_instance.id, workflow_instance.status_id, workflow_instance.start_date, workflow_instance.end_date))
                for action_instance in workflow_instance.action_instances:
                    print("    action: {}, Status: {}, Start Date: {}, End Date: {}, Order: {}, Slice: {}".format(action_instance.id, action_instance.status_id, action_instance.start_date, action_instance.end_date, action_instance.order, action_instance.slice))

    def _testing_check_verify(self, objects, expected):
        workflow_engine = InstanceWorkflowEngine(Mock(), Mock())
        workflow_engine.status_cache[StatusConstants.NEW] = Status(id=StatusConstants.NEW, name="Test NEW", type=StatusTypes.SUCCESS)
        workflow_engine.status_cache[StatusConstants.SUCCESS] = Status(id=StatusConstants.SUCCESS, name="Test SUCCESS", type=StatusTypes.SUCCESS)
        workflow_engine.status_cache[StatusConstants.FAILED] = Status(id=StatusConstants.FAILED, name="Test FAILED", type=StatusTypes.FAILED)
        workflow_engine.status_cache[StatusConstants.CANCELED] = Status(id=StatusConstants.NEW, name="Test CANCELED", type=StatusTypes.CANCELED)

        if expected[2]:
            workflow_engine.status_cache[expected[2].id] = expected[2]

        all_complete, all_passed, failed_type = workflow_engine._check_and_verify_statuses(objects)

        eq_(expected[0], all_complete, "All Complete did not match")
        eq_(expected[1], all_passed, "All passed did not match.")
        eq_(expected[2], failed_type, "Failed Type did not match.")

    def _pipeline_helper(self):
        action_instance = ActionInstance(id=1, order=0)
        workflow_instance = WorkflowInstance(id=1, actions=[action_instance])
        stage_instance = StageInstance(id=1, workflows=[workflow_instance])
        pipeline_instance = PipelineInstance(id=1, stages=[stage_instance, stage_instance])

        return action_instance, workflow_instance, stage_instance, pipeline_instance

    def _build_pipeline_instance(self, actions, completed=False):
        pipeline_instance = PipelineInstance()
        status_id = StatusConstants.NEW if not completed else StatusConstants.SUCCESS

        if completed:
            pipeline_instance.created_date = datetime.datetime.utcnow()
            pipeline_instance.start_date = datetime.datetime.utcnow()
            pipeline_instance.end_date = datetime.datetime.utcnow()
            pipeline_instance.status_id = status_id

        stage_instances = {}

        s_idcount = w_idcount = a_idcount = 1
        pipeline_instance.pipeline = Mock(stages=[])

        for action in actions:
            sp = action.split(':')

            stage_instance = StageInstance(id=s_idcount, status_id=status_id)
            stage_instances[s_idcount] = stage_instance

            if completed:
                stage_instance.created_date = datetime.datetime.utcnow()
                stage_instance.start_date = datetime.datetime.utcnow()
                stage_instance.end_date = datetime.datetime.utcnow()

            w_number = int(sp[0])
            a_sp = sp[1].split('-')
            for workflow_id in range(0, w_number):
                workflow_instance = WorkflowInstance(id=w_idcount, stage_instance_id=stage_instance.id, status_id=status_id)

                if completed:
                    workflow_instance.created_date = datetime.datetime.utcnow()
                    workflow_instance.start_date = datetime.datetime.utcnow()
                    workflow_instance.end_date = datetime.datetime.utcnow()

                try:
                    order = 0
                    for action_count in a_sp[workflow_id].split(','):
                        a_count = int(action_count)
                        for num in range(0, a_count):
                            action_instance = ActionInstance(id=a_idcount, order=order, slice="{}/{}".format(num+1, a_count), workflow_instance_id=workflow_instance.id, status_id=status_id)
                            if completed:
                                action_instance.created_date = datetime.datetime.utcnow()
                                action_instance.start_date = datetime.datetime.utcnow()
                                action_instance.end_date = datetime.datetime.utcnow()

                            workflow_instance.action_instances.append(action_instance)
                            a_idcount += 1
                        order += 1
                except:
                    action_instance = ActionInstance(id=a_idcount, order=0, workflow_instance_id=workflow_instance.id, status_id=status_id)
                    if completed:
                        action_instance.created_date = datetime.datetime.utcnow()
                        action_instance.start_date = datetime.datetime.utcnow()
                        action_instance.end_date = datetime.datetime.utcnow()

                    workflow_instance.action_instances.append()
                w_idcount += 1
                stage_instance.workflow_instances.append(workflow_instance)
            pipeline_instance.stage_instances.append(stage_instance)
            pipeline_instance.pipeline.stages.append(stage_instance)

            s_idcount += 1
        return pipeline_instance

    @staticmethod
    def _get_mocked_dal():
        mocked_dal = Mock()

        def mocked_get(id):
            return {9: Status(id=9, name="UNSTABLE", display_name='Unstable', type=StatusTypes.FAILED),
                    8: Status(id=8, name="CANCELED", display_name='Canceled', type=StatusTypes.FAILED),
                    4: Status(id=4, name="SUCCESS", display_name='Success', type=StatusTypes.SUCCESS),
                    5: Status(id=5, name="FAILED", display_name='Failed', type=StatusTypes.FAILED),
                    2: Status(id=2, name="READY", display_name='Ready', type=StatusTypes.SUCCESS)}[id]
        mocked_dal.get_status_by_id = mocked_get
        return mocked_dal
