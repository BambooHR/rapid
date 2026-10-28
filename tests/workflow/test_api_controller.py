try:
    import simplejson as json
except ImportError:
    import json

from ddt import ddt, data
from flask import Flask
from mock.mock import MagicMock, patch
from sqlalchemy.orm.exc import NoResultFound
from werkzeug.test import Client

from rapid.lib.constants import Constants
from rapid.lib.exceptions import InvalidObjectException
from tests.framework.unit_test import UnitTest
from rapid.workflow.api_controller import APIRouter


@ddt
class TestAPIController(UnitTest):

    def setUp(self):
        self.controller = self.fill_object_with_mocks(APIRouter)

    @patch.object(APIRouter, APIRouter._de_obfuscate_id.__name__)
    def test_get_cursor_logic_get_from_header(self, mock_util):
        mock_request = MagicMock()
        mock_util.return_value = '123456'

        self.controller.http_wrapper.current_request.return_value = mock_request
        mock_header = MagicMock()
        mock_header.get.return_value = '123456'
        mock_request.headers = mock_header

        self.assertEqual('123456', self.controller._get_cursor())
        mock_util.assert_called_once_with('123456')
        mock_header.get.assert_called_with(Constants.CONTINUATION_HEADER, None)

    @patch.object(APIRouter, APIRouter._de_obfuscate_id.__name__)
    def test_get_cursor_logic_get_from_json_post(self, mock_util):
        mock_request = MagicMock()
        mock_util.return_value = '123456'
        mock_request.get_json.return_value = {'continuation_token': '123456'}

        self.controller.http_wrapper.current_request.return_value = mock_request
        mock_header = MagicMock()
        mock_header.get.return_value = None
        mock_request.headers = mock_header

        self.assertEqual('123456', self.controller._get_cursor())
        mock_util.assert_called_once_with('123456')

    @patch.object(APIRouter, APIRouter._de_obfuscate_id.__name__)
    @patch.object(APIRouter, APIRouter._get_args.__name__)
    def test_get_cursor_logic_get_from_args(self, mock_args, mock_util):
        mock_request = MagicMock()
        mock_util.return_value = '123456'
        mock_args.return_value = {'continuation_token': '123456'}

        self.assertEqual('123456', self.controller._get_cursor())

    def _list_single_object(self, one_result):
        session = MagicMock()
        query = MagicMock()
        session.query.return_value.filter.return_value = query
        if isinstance(one_result, Exception):
            query.one.side_effect = one_result
        else:
            query.one.return_value = one_result

        APIRouter.class_map['pipelines'] = MagicMock()
        with patch('rapid.workflow.api_controller.get_db_session', return_value=iter([session])), \
                patch.object(APIRouter, APIRouter._is_valid.__name__, return_value=True), \
                patch.object(APIRouter, APIRouter._get_additional_fields.__name__,
                             side_effect=lambda clazz, _query: ({}, _query)):
            return self.controller.list_single_object('pipelines', 9999999)

    def test_list_single_object_missing_id_returns_json_404(self):
        response = self._list_single_object(NoResultFound('No row was found when one was required'))

        self.assertEqual(404, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual({'message': 'Entity not found'}, json.loads(response.get_data(as_text=True)))

    def test_list_single_object_found_returns_serialized_instance(self):
        instance = MagicMock()
        instance.serialize.return_value = {'id': 1}

        response = self._list_single_object(instance)

        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual({'id': 1}, json.loads(response.get_data(as_text=True)))

    def test_list_single_object_invalid_endpoint_returns_404(self):
        with patch.object(APIRouter, APIRouter._is_valid.__name__, return_value=False):
            response = self.controller.list_single_object('not_a_thing', 1)

        self.assertEqual(404, response.status_code)

    def test_reset_single_action_instance_route_returns_outcome(self):
        service = self.controller.action_instance_service
        service.reset_action_instance.return_value = {'action_instance_id': 12, 'outcome': 'reset'}

        response = self._post_reset_single('rapid-key')

        self.assertEqual(200, response.status_code)
        self.assertEqual({'action_instance_id': 12, 'outcome': 'reset'}, json.loads(response.get_data(as_text=True)))
        service.reset_action_instance.assert_called_once_with(12, False, reset_single_slice=True)
        service.reset_single_action_instance.assert_not_called()

    @data(404, 409)
    def test_reset_single_action_instance_route_preserves_error_status(self, code):
        self.controller.action_instance_service.reset_action_instance.side_effect = InvalidObjectException('Rejected', code)

        response = self._post_reset_single('rapid-key')

        self.assertEqual(code, response.status_code)
        self.assertEqual({'message': 'Rejected'}, json.loads(response.get_data(as_text=True)))

    def test_reset_single_action_instance_route_requires_api_key(self):
        response = self._post_reset_single('wrong-key')

        self.assertEqual(401, response.status_code)
        self.controller.action_instance_service.reset_single_action_instance.assert_not_called()

    def _post_reset_single(self, api_key, payload=None):
        flask_app = Flask(__name__)
        flask_app.rapid_config = MagicMock(api_key='rapid-key')
        self.controller.register_url_rules(flask_app)
        from flask import request
        self.controller.http_wrapper.current_request.side_effect = lambda: request
        return Client(flask_app).post('/api/action_instances/12/reset', json={'reset_single_slice': True} if payload is None else payload, headers={'X-Rapidci-Api-Key': api_key})


    @data({'complete_reset': 'false'}, {'reset_single_slice': 'false'}, {'reset_single_slice': 0}, {'complete_reset': True, 'reset_single_slice': True})
    def test_reset_rejects_missing_or_non_boolean_scope(self, payload):
        self.controller.http_wrapper.current_request.return_value.get_json.return_value = payload
        response = self._post_reset_single('rapid-key', payload)
        self.assertEqual(400, response.status_code)
        self.controller.action_instance_service.reset_action_instance.assert_not_called()

    @data({}, {'complete_reset': False}, {'complete_reset': True}, {'reset_single_slice': False})
    def test_legacy_reset_payload_keeps_existing_behavior(self, payload):
        self.controller.action_instance_service.reset_action_instance.return_value = True
        response = self._post_reset_single('rapid-key', payload)
        self.assertEqual(200, response.status_code)
        self.assertEqual({'message': 'Action instance reset'}, json.loads(response.get_data(as_text=True)))
        self.controller.action_instance_service.reset_action_instance.assert_called_once_with(12, payload.get('complete_reset', False), reset_single_slice=False)
