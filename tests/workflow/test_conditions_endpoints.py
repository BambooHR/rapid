import json
from unittest.mock import MagicMock, patch

from rapid.workflow.api_controller import APIRouter
from tests.framework.unit_test import UnitTest


class TestPipelineActionConditionsEndpoints(UnitTest):
    def setUp(self):
        self.controller = self.fill_object_with_mocks(APIRouter)
        self.request = MagicMock()
        self.controller.http_wrapper.current_request.return_value = self.request

        self.fake_session = MagicMock()
        self.get_db_session_patcher = patch('rapid.workflow.api_controller.get_db_session', return_value=[self.fake_session])
        self.get_db_session_patcher.start()
        self.addCleanup(self.get_db_session_patcher.stop)
        self.controller._load_objects()
        self.dal = MagicMock()

    def test_endpoints_are_discoverable(self):
        assert self.controller._is_valid('pipeline_action_conditions')
        assert self.controller._is_valid('action_instance_conditions')

    def test_metadata_available_for_new_models(self):
        resp = self.controller.metadata('pipeline_action_conditions')
        data = json.loads(resp.get_data(as_text=True))

        assert 'pipeline_id' in data
        assert 'action_id' in data
        assert 'status_id' in data
        assert 'expression' in data

        resp = self.controller.metadata('action_instance_conditions')

        data = json.loads(resp.get_data(as_text=True))
        assert 'action_instance_id' in data
        assert 'pipeline_id' in data
        assert 'action_id' in data
        assert 'status_id' in data
        assert 'expression' in data

    @patch.object(APIRouter, APIRouter._retrieve_dal.__name__)
    def test_pipeline_action_conditions_create(self, mock_retrieve_dal):
        body = {"pipeline_id": 1, "action_id": 2, "status_id": 9, "expression": "x == 1"}
        self.request.get_json.return_value = body

        self.dal.create_object.return_value = {"id": 123, **body}
        mock_retrieve_dal.return_value = self.dal

        resp = self.controller.create('pipeline_action_conditions')

        data = json.loads(resp.get_data(as_text=True))
        assert data['id'] == 123
        assert data['pipeline_id'] == 1
        self.dal.create_object.assert_called()

    @patch.object(APIRouter, APIRouter._retrieve_dal.__name__)
    def test_pipeline_action_conditions_edit(self, mock_retrieve_dal):
        self.request.json = {"expression": "x == 2"}

        instance = MagicMock()
        instance.serialize.return_value = {"id": 123, "expression": "x == 2"}
        self.dal.edit_object.return_value = instance
        mock_retrieve_dal.return_value = self.dal

        resp = self.controller.edit_object('pipeline_action_conditions', 123)

        data = json.loads(resp.get_data(as_text=True))
        assert data['id'] == 123
        assert data['expression'] == 'x == 2'
        self.dal.edit_object.assert_called()

    @patch.object(APIRouter, APIRouter._retrieve_dal.__name__)
    def test_pipeline_action_conditions_delete(self, mock_retrieve_dal):
        instance = MagicMock()
        instance.serialize.return_value = {"id": 123}
        self.dal.delete_object.return_value = instance
        mock_retrieve_dal.return_value = self.dal

        resp = self.controller.delete_object('pipeline_action_conditions', 123)

        data = json.loads(resp.get_data(as_text=True))
        assert data['id'] == 123
        self.dal.delete_object.assert_called()

    @patch.object(APIRouter, APIRouter._retrieve_dal.__name__)
    def test_action_instance_conditions_create(self, mock_retrieve_dal):
        body = {"action_instance_id": 1, "pipeline_id": 2, "action_id": 3, "status_id": 9, "expression": "x == 1"}
        self.request.get_json.return_value = body

        self.dal.create_object.return_value = {"id": 456, **body}
        mock_retrieve_dal.return_value = self.dal

        resp = self.controller.create('action_instance_conditions')

        data = json.loads(resp.get_data(as_text=True))
        assert data['id'] == 456
        assert data['action_instance_id'] == 1
        assert data['pipeline_id'] == 2
        assert data['action_id'] == 3
        assert data['status_id'] == 9
        assert data['expression'] == 'x == 1'
        self.dal.create_object.assert_called()

    @patch.object(APIRouter, APIRouter._retrieve_dal.__name__)
    def test_action_instance_conditions_edit(self, mock_retrieve_dal):
        self.request.json = {"expression": "x == 3"}

        instance = MagicMock()
        instance.serialize.return_value = {"id": 456, "expression": "x == 3"}
        self.dal.edit_object.return_value = instance
        mock_retrieve_dal.return_value = self.dal

        resp = self.controller.edit_object('action_instance_conditions', 456)

        data = json.loads(resp.get_data(as_text=True))
        assert data['id'] == 456
        assert data['expression'] == 'x == 3'
        self.dal.edit_object.assert_called()

    @patch.object(APIRouter, APIRouter._retrieve_dal.__name__)
    def test_action_instance_conditions_delete(self, mock_retrieve_dal):
        instance = MagicMock()
        instance.serialize.return_value = {"id": 456}
        self.dal.delete_object.return_value = instance
        mock_retrieve_dal.return_value = self.dal

        resp = self.controller.delete_object('action_instance_conditions', 456)

        data = json.loads(resp.get_data(as_text=True))
        assert data['id'] == 456
        self.dal.delete_object.assert_called()
