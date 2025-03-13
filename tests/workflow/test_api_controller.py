from mock.mock import MagicMock, patch

from rapid.lib.constants import Constants
from tests.framework.unit_test import UnitTest
from rapid.workflow.api_controller import APIRouter


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
