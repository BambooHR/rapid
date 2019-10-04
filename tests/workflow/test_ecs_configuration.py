from unittest import TestCase

from mock import patch, Mock

from rapid.workflow.queue_handlers.container_handlers.ecs_configuration import ECSConfiguration


class TestECSConfiguration(TestCase):
    def test_aws_credentials(self):
        config = ECSConfiguration()
        config.aws_session_token = 'token'
        config.aws_access_key_id = 'key'
        config.aws_secret_access_key = 'secret'

        self.assertEqual({'aws_session_token': 'token',
                          'aws_access_key_id': 'key',
                          'aws_secret_access_key': 'secret'}, config.aws_credentials)

    @patch('rapid.workflow.queue_handlers.container_handlers.ecs_configuration.ECSConfiguration._get_section_values')
    def test_default_task_definition_calls_correctly(self, section):
        config = ECSConfiguration()
        section.return_value = 'foo'
        self.assertEqual('foo', config.default_task_definition)

    @patch('rapid.workflow.queue_handlers.container_handlers.ecs_configuration.json')
    def test_handle_normal_value_list_uses_json_load(self, mock_json):
        mock = Mock()
        mock.get.return_value = 'foobar'
        config = ECSConfiguration()
        config._handle_normal_value(mock, 'key', 'section', list)
        mock_json.loads.assert_called_with('foobar')

    @patch('rapid.workflow.queue_handlers.container_handlers.ecs_configuration.json')
    def test_handle_normal_value_dict_uses_json_load(self, mock_json):
        mock = Mock()
        mock.get.return_value = 'foobar'
        config = ECSConfiguration()
        config._handle_normal_value(mock, 'key', 'section', dict)
        mock_json.loads.assert_called_with('foobar')

    def test_handle_normal_value_error_calls_standard_set_value(self):
        mock = Mock()
        mock.side_effect = [ValueError(), 'oh-yeah']
        config = ECSConfiguration()
        config._handle_normal_value(Mock(), 'foo', 'bar', mock)
        self.assertEqual('oh-yeah', config.foo)

