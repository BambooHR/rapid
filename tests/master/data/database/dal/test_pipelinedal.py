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
from rapid.lib.Constants import StatusConstants
from rapid.lib.Exceptions import InvalidObjectException

try:
    import simplejson as json
except:
    import json

from unittest import TestCase

from mock.mock import Mock, patch
from nose.tools import eq_

from rapid.workflow.data.dal.PipelineDal import PipelineDal


class TestPipelineDal(TestCase):

    def setUp(self):
        self.dal = PipelineDal(Mock())

    def test_get_actions_empty(self):
        eq_([], self.dal.get_actions({}, None, None, Mock()))

    def test_get_actions_data(self):
        action_json = {'cmd': 'something'}

        actions = self.dal.get_actions({'actions': [action_json]}, Mock(id=1), Mock(id=2), Mock())
        for key, value in {'cmd': 'something', 'pipeline_id': 1, 'workflow_id': 2, 'order': 0}.iteritems():
            eq_(value, getattr(actions[0], key))

    def test_get_workflows_empty(self):
        eq_([], self.dal.get_workflows({}, None, None, Mock()))

    def test_get_workflows_data_no_actions(self):
        workflow_json = {'name': 'foo', 'active': True}

        workflows = self.dal.get_workflows({'workflows': [workflow_json]}, Mock(id=1), Mock(id=2), Mock())
        for key, value in {'name': 'foo', 'active': True, "stage_id": 2, "order": 0, "actions": []}.iteritems():
            eq_(value, getattr(workflows[0], key))

    def test_get_workflows_data_with_actions(self):
        workflow_json = {'name': 'foo', 'active': True, 'actions': [{'cmd': 'something'}]}

        workflows = self.dal.get_workflows({'workflows': [workflow_json]}, Mock(id=1), Mock(id=2), Mock())
        for key, value in {'name': 'foo', 'active': True, "stage_id": 2, "order": 0, "actions": 1 }.iteritems():
            if key == 'actions':
                eq_(value, len(getattr(workflows[0], 'actions')))
            else:
                eq_(value, getattr(workflows[0], key))

    def test_get_stages_empty(self):
        eq_([], self.dal.get_stages({}, None, None))

    def test_get_stages_data_no_workflows(self):
        stage_json = {'name': 'foostage', 'active': True}

        stages = self.dal.get_stages({'stages': [stage_json]}, Mock(id=1), Mock())
        for key, value in {'name': 'foostage', 'active': True, 'pipeline_id': 1, 'order': 0}.iteritems():
            eq_(value, getattr(stages[0], key))

    def test_get_stages_data_with_workflows(self):
        stage_json = {'name': 'foostage', 'active': True, 'workflows': [{'name': 'foo', 'active': True, 'actions': []}]}

        stages = self.dal.get_stages({'stages': [stage_json]}, Mock(id=1), Mock())
        for key, value in {'name': 'foostage', 'active': True, 'pipeline_id': 1, 'order': 0, 'workflows': 1}.iteritems():
            if 'workflows' == key:
                eq_(value, len(getattr(stages[0], key)))
            else:
                eq_(value, getattr(stages[0], key))

    def test_get_pipeline_no_json(self):
        with self.assertRaises(BaseException) as cm:
            self.dal._get_pipeline(None)
        self.assertEqual("No pipeline was created.", cm.exception.message)

    def test_get_pipeline_with_json(self):
        self.dal.app = Mock()
        pipeline = self.dal._get_pipeline({"name": "something", "active": True})

        eq_({"name": "something", "active": True, "id": None}, json.loads(pipeline))

    def _register_helper(self, uri, name, func, methods):
        if not hasattr(self, 'registry'):
            self.registry = {}
        self.registry[uri] = {'name': name, 'func': func.func_name, 'methods': methods}

    def test_register_url_rules(self):
        mock_app = Mock()
        mock_app.add_url_rule = self._register_helper
        self.dal.register_url_rules(mock_app)

        eq_(self.dal.app, mock_app)
        eq_(self.registry['/api/pipelines/create'], {'name': 'create_pipeline', 'func': 'create_pipeline', 'methods': ['POST']})
        eq_(self.registry['/api/pipelines/<int:pipeline_id>/start'], {'name': 'start_pipeline_instance', 'func': 'start_pipeline_instance', 'methods': ['POST']})

    @patch('rapid.workflow.data.dal.PipelineDal.PipelineDal.get_pipeline_instance_by_id')
    @patch('rapid.workflow.data.dal.PipelineDal.get_db_session')
    def test_cancel_pipeline_instance_returns_404_if_invalid(self, db_session, pipeline_instance_by_id):
        """
        @rapid-unit Workflow:Cancel Pipeline Instance:Should indicate not found if instance not found
        :return:
        :rtype:
        """
        pipeline_instance_by_id.return_value = None
        db_session.return_value = [Mock()]
        
        with self.assertRaises(InvalidObjectException) as exception:
            self.dal.cancel_pipeline_instance(12345)

        eq_(404, exception.exception.code)
        eq_("Pipeline Instance not found", exception.exception.description)

    @patch('rapid.workflow.data.dal.PipelineDal.StoreService')
    @patch('rapid.workflow.data.dal.PipelineDal.PipelineDal.get_pipeline_instance_by_id')
    @patch('rapid.workflow.data.dal.PipelineDal.get_db_session')
    def test_cancel_pipeline_instance_cancels_current_running_clients(self, db_session, pipeline_instance_by_id, store_service):
        """
        @rapid-unit Workflow:Cancel Pipeline Instance:Should cancel current assigned clients
        :return:
        :rtype:
        """
        db_session.return_value = [Mock()]
        mock_pipeline_instance = Mock()
        client1 = Mock()
        client1.get_uri.return_value = '12345'

        client2 = Mock()
        store_service.get_clients.return_value = {"12345": client1, "54321": client2}

        mock_pipeline_instance.action_instances = [Mock(assigned_to="12345", status_id=StatusConstants.INPROGRESS),
                                                   Mock(assinged_to="12345", status_id=StatusConstants.SUCCESS),
                                                   Mock(assinged_to="12345", status_id=StatusConstants.FAILED),
                                                   Mock(assigned_to="other", status_id=StatusConstants.INPROGRESS)]
        pipeline_instance_by_id.return_value = mock_pipeline_instance

        self.dal.app = Mock(rapid_config=Mock(verify_certs=False))

        eq_("Running clients have been canceled and pipeline canceled.", self.dal.cancel_pipeline_instance(12345)['message'])
        
        eq_(1, client1.cancel_work.call_count)
        eq_(0, client2.cancel_work.call_count)

