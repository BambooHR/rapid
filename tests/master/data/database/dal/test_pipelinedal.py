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
from rapid.lib.constants import StatusConstants
from rapid.lib.exceptions import InvalidObjectException
from tests.framework.unit_test import UnitTest

try:
    import simplejson as json
except:
    import json

from mock.mock import Mock, patch

from rapid.workflow.data.dal.pipeline_dal import PipelineDal


class TestPipelineDal(UnitTest):

    def setUp(self):
        self.mock_constants = Mock()
        self.dal = PipelineDal(Mock(), self.mock_constants)

    def test_get_actions_empty(self):
        self.assertEqual([], self.dal.get_actions({}, None, None, Mock()))

    def test_get_actions_data(self):
        action_json = {'cmd': 'something'}

        actions = self.dal.get_actions({'actions': [action_json]}, Mock(id=1), Mock(id=2), Mock())
        for key, value in {'cmd': 'something', 'pipeline_id': 1, 'workflow_id': 2, 'order': 0}.items():
            self.assertEqual(value, getattr(actions[0], key))

    def test_get_workflows_empty(self):
        self.assertEqual([], self.dal.get_workflows({}, None, None, Mock()))

    def test_get_workflows_data_no_actions(self):
        workflow_json = {'name': 'foo', 'active': True}

        workflows = self.dal.get_workflows({'workflows': [workflow_json]}, Mock(id=1), Mock(id=2), Mock())
        for key, value in {'name': 'foo', 'active': True, "stage_id": 2, "order": 0, "actions": []}.items():
            self.assertEqual(value, getattr(workflows[0], key))

    def test_get_workflows_data_with_actions(self):
        workflow_json = {'name': 'foo', 'active': True, 'actions': [{'cmd': 'something'}]}

        workflows = self.dal.get_workflows({'workflows': [workflow_json]}, Mock(id=1), Mock(id=2), Mock())
        for key, value in {'name': 'foo', 'active': True, "stage_id": 2, "order": 0, "actions": 1 }.items():
            if key == 'actions':
                self.assertEqual(value, len(getattr(workflows[0], 'actions')))
            else:
                self.assertEqual(value, getattr(workflows[0], key))

    def test_get_stages_empty(self):
        self.assertEqual([], self.dal.get_stages({}, None, None))

    def test_get_stages_data_no_workflows(self):
        stage_json = {'name': 'foostage', 'active': True}

        stages = self.dal.get_stages({'stages': [stage_json]}, Mock(id=1), Mock())
        for key, value in {'name': 'foostage', 'active': True, 'pipeline_id': 1, 'order': 0}.items():
            self.assertEqual(value, getattr(stages[0], key))

    def test_get_stages_data_with_workflows(self):
        stage_json = {'name': 'foostage', 'active': True, 'workflows': [{'name': 'foo', 'active': True, 'actions': []}]}

        stages = self.dal.get_stages({'stages': [stage_json]}, Mock(id=1), Mock())
        for key, value in {'name': 'foostage', 'active': True, 'pipeline_id': 1, 'order': 0, 'workflows': 1}.items():
            if 'workflows' == key:
                self.assertEqual(value, len(getattr(stages[0], key)))
            else:
                self.assertEqual(value, getattr(stages[0], key))

    def test_get_pipeline_no_json(self):
        with self.assertRaises(BaseException) as cm:
            self.dal._get_pipeline(None)
        self.assertEqual("No pipeline was created.", str(cm.exception))

    @patch('rapid.workflow.data.dal.pipeline_dal.get_db_session')
    def test_get_pipeline_with_json(self, get_db_session):
        self.dal.app = Mock()
        get_db_session.return_value = [Mock()]
        pipeline = self.dal._get_pipeline({"name": "something", "active": True})

        self.assertEqual({"name": "something", "active": True, "id": None}, json.loads(pipeline))

    def _register_helper(self, uri, name, func, methods):
        if not hasattr(self, 'registry'):
            self.registry = {}
        self.registry[uri] = {'name': name, 'func': func.__name__, 'methods': methods}

    def test_register_url_rules(self):
        mock_app = Mock()
        mock_app.add_url_rule = self._register_helper
        self.dal.register_url_rules(mock_app)

        self.assertEqual(self.dal.app, mock_app)
        self.assertEqual(self.registry['/api/pipelines/create'], {'name': 'create_pipeline', 'func': 'create_pipeline', 'methods': ['POST']})
        self.assertEqual(self.registry['/api/pipelines/<int:pipeline_id>/start'], {'name': 'start_pipeline_instance', 'func': 'start_pipeline_instance', 'methods': ['POST']})

    @patch('rapid.workflow.data.dal.pipeline_dal.PipelineDal.get_pipeline_instance_by_id')
    @patch('rapid.workflow.data.dal.pipeline_dal.get_db_session')
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

        self.assertEqual(404, exception.exception.code)
        self.assertEqual("Pipeline Instance not found", exception.exception.description)

    @patch('rapid.workflow.data.dal.pipeline_dal.StoreService')
    @patch('rapid.workflow.data.dal.pipeline_dal.PipelineDal.get_pipeline_instance_by_id')
    @patch('rapid.workflow.data.dal.pipeline_dal.get_db_session')
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

        self.assertEqual("Running clients have been canceled and pipeline canceled.", self.dal.cancel_pipeline_instance(12345)['message'])

        self.mock_constants.cancel_worker.assert_called_with(mock_pipeline_instance.action_instances[0].serialize())
        

