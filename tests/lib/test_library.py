from unittest import TestCase

from mock import patch, Mock

from rapid.lib import setup_logging, basic_auth


class TestLibrary(TestCase):
    @patch('rapid.lib.logging')
    def test_setup_logging_stream_default_stream(self, logging):
        mock_app = Mock(rapid_config=Mock(log_file=None))
        setup_logging(mock_app)
        self.assertEqual(1, logging.StreamHandler.call_count)
        self.assertEqual(0, logging.FileHandler.call_count)

    @patch('rapid.lib.logging')
    def test_setup_logging_file_when_exists(self, logging):
        mock_app = Mock(rapid_config=Mock(log_file='Something'))
        setup_logging(mock_app)
        logging.FileHandler.assert_called_with('Something')

    @patch('rapid.lib.get_current_app')
    @patch('rapid.lib.get_current_request')
    def test_basic_auth_wrapper_calls_when_successful(self, request, current_app):
        to_call = self.__setup_basic_auth_test()
        mock = Mock(basic_auth_user='foo', basic_auth_pass='bar')
        current_app.return_value = Mock(rapid_config=mock)
        request.return_value = Mock(authorization={'username': 'foo', 'password': 'bar'})
        with self.assertRaises(Exception) as exception:
            to_call()

    @patch('rapid.lib.get_current_app')
    @patch('rapid.lib.get_current_request')
    def test_basic_auth_wrapper_returns_when_doesnt_match(self, request, current_app):
        to_call = self.__setup_basic_auth_test()
        mock = Mock(basic_auth_user='foo', basic_auth_pass='bad_pass')
        current_app.rapid_config = mock
        request.authorization = {'username': 'foo', 'password': 'bar'}
        ret = to_call()
        self.assertEqual(401, ret.status_code)

    def __setup_basic_auth_test(self):
        def testing():
            raise Exception("YAY!")

        return basic_auth(testing)
