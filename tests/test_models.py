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
from unittest import TestCase

from ddt import ddt, data
from nose.tools.trivial import eq_, ok_

from rapid.workflow.data.models import Pipeline, Stage, Workflow, PipelineInstance, StageInstance, WorkflowInstance, Action, ActionInstance


@ddt
class TestModels(TestCase):
    mapping = {
        Pipeline: {'clz': PipelineInstance, 'parent_id': 'pipeline_id'},
        Stage: {'clz': StageInstance, 'parent_id': 'stage_id', 'check_fields': {'order': 1}},
        Workflow: {'clz': WorkflowInstance, 'parent_id': 'workflow_id', 'check_fields': {'order': 1}},
        Action: {'clz': ActionInstance, 'parent_id': 'action_id', 'check_fields': {'cmd': 'bogus',
                                                                                   'executable': 'something',
                                                                                   'args': '',
                                                                                   'manual': False,
                                                                                   'callback_required': False,
                                                                                   'grain': 'trial'}}
    }

    @data(Pipeline, Stage, Workflow)
    def test_active_model_objects(self, model):
        model_instance = model(name='Testing', active=False)

        assert 'Testing' == model_instance.name
        assert False == model_instance.active
        assert "{}s".format(model_instance.__class__.__name__.lower()) == model_instance.__tablename__

    @data(Pipeline, Stage, Workflow, Action)
    def test_convert_to_instance(self, model):
        model_map = self.mapping[model]
        additional_kws = model_map['check_fields'] if 'check_fields' in model_map else {}
        model_instance = model(name='Testing', id=1, **additional_kws)

        instance_conversion = model_instance.convert_to_instance()
        ok_(model_map['clz'] == type(instance_conversion))
        eq_(1, getattr(instance_conversion, model_map['parent_id']))

        if 'check_fields' in model_map:
            for key, value in model_map['check_fields'].items():
                eq_(value, getattr(instance_conversion, key))
