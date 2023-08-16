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
from mock.mock import Mock

from rapid.workflow.workflow_engine import WorkflowEngine
from rapid.workflow.data.models import Pipeline, Stage, Action, Workflow
from tests.framework.unit_test import UnitTest


class TestWorkflowEngine(UnitTest):

    def test_init(self):
        workflow_engine = WorkflowEngine(Pipeline())

        self.assertEqual(Pipeline, workflow_engine.pipeline_class)
        self.assertEqual(Stage, workflow_engine.stage_class)
        self.assertEqual(Workflow, workflow_engine.workflow_class)
        self.assertEqual(Action, workflow_engine.action_class)

    def test_load_pipeline(self):
        action, workflow, stage, pipeline = self._pipeline_helper()

        workflow_engine = WorkflowEngine(pipeline)
        loaded_pipeline = workflow_engine._load_pipeline()

        self.assertEqual(pipeline, workflow_engine.pipeline)
        self.assertEqual(pipeline, loaded_pipeline)
        self.assertEqual({1: stage}, workflow_engine.stage_mapper)
        self.assertEqual({1: workflow}, workflow_engine.workflow_mapper)
        self.assertEqual({1: action}, workflow_engine.action_mapper)

    def test_get_stage(self):
        action, workflow, stage, pipeline = self._pipeline_helper()

        workflow_engine = WorkflowEngine(pipeline)
        self.assertEqual(stage, workflow_engine._get_stage(1))

    def test_get_workflow(self):
        action, workflow, stage, pipeline = self._pipeline_helper()

        workflow_engine = WorkflowEngine(pipeline)
        self.assertEqual(workflow, workflow_engine._get_workflow(1))

    def test_get_action(self):
        action, workflow, stage, pipeline = self._pipeline_helper()

        workflow_engine = WorkflowEngine(pipeline)

        self.assertEqual(action, workflow_engine._get_action(1))

    def test_get_stages(self):
        stage = Stage()
        pipeline = Pipeline(stages=[stage])

        workflow_engine = WorkflowEngine(pipeline)
        self.assertEqual([stage], workflow_engine._get_stages(pipeline))

    def test_get_workflows(self):
        workflow = Workflow()
        stage = Stage(workflows=[workflow])

        workflow_engine = WorkflowEngine(Mock())
        self.assertEqual([workflow], workflow_engine._get_workflows(stage))

    def test_get_actions(self):
        action = Action()
        workflow = Workflow(actions=[action])
        workflow_engine = WorkflowEngine(Mock())
        self.assertEqual([action], workflow_engine._get_actions(workflow))

    def test_get_workflows_by_stage_id(self):
        action, workflow, stage, pipeline = self._pipeline_helper()

        workflow_engine = WorkflowEngine(pipeline)

        self.assertEqual([workflow], workflow_engine._get_workflows_by_stage_id(1))

    def test_get_actions_by_workflow_id(self):
        action, workflow, stage, pipeline = self._pipeline_helper()

        workflow_engine = WorkflowEngine(pipeline)

        self.assertEqual([action], workflow_engine._get_actions_by_workflow_id(1))

    def _pipeline_helper(self):
        action = Action(id=1)
        workflow = Workflow(id=1, actions=[action])
        stage = Stage(id=1, workflows=[workflow])
        pipeline = Pipeline(id=1, stages=[stage])

        return action, workflow, stage, pipeline
