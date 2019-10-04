from unittest import TestCase

from mock import patch, Mock

from rapid.workflow.queue_handlers.container_handlers.docker_configuration import DockerConfiguration


class TestDockerConfiguration(TestCase):
    def test_can_add_acceptable_data(self):
        config = DockerConfiguration(**{'add-host': 'testing', 'env': 'environment', 'volume': "vol", 'bad': 'no_worky'})
        self.assertEqual('testing', getattr(config, 'add-host'))
        self.assertEqual('environment', config.env)
        self.assertEqual('vol', config.volume)
        self.assertFalse(hasattr(config, 'bad'))

    @patch('rapid.workflow.queue_handlers.container_handlers.docker_configuration.DockerConfiguration._get_substituted_value')
    def test_get_string_rep(self, sub_value):
        def req_value(self, value):
            return value

        sub_value.side_effect = req_value

        config = DockerConfiguration(**{'add-host': 'host', 'env': ['environ', 'environ2'], 'volume': 'volu'})
        self.assertEqual('--add-host=host --env=environ --env=environ2 --volume=volu', config.get_string_rep(Mock()))

    def test_get_substituted_value(self):
        config = DockerConfiguration()
        self.assertEqual('action_id=12356', config._get_substituted_value(Mock(action_id='12356'), '(action_id)'))
