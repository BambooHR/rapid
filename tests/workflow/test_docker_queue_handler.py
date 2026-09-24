import os
from unittest import TestCase

from mock import Mock, patch

from rapid.workflow.queue_handlers.handlers.docker_queue_handler import DockerQueueHandler


class TestDockerQueueHandler(TestCase):
    def setUp(self):
        self.master_config = Mock()
        self.action_instance_service = Mock()
        self.handler = DockerQueueHandler(self.master_config, self.action_instance_service)

    def test_container_identifier(self):
        self.assertEqual('docker', self.handler.container_identifier)

    def _work_request(self, environment):
        self.master_config.workspace = '/tmp/ws'
        return Mock(
            environment=environment,
            pipeline_instance_id=2,
            action_instance_id=1,
            workflow_instance_id=3,
            slice='1/1',
        )

    @patch.dict(os.environ, {'TERM': 'dumb'}, clear=True)
    def test_get_environment_keeps_job_color_values_stored_as_bytes(self):
        env = self.handler.get_environment(self._work_request({'FORCE_COLOR': '0', 'TERM': 'dumb'}))
        self.assertEqual(b'0', env[b'FORCE_COLOR'])
        self.assertNotIn('FORCE_COLOR', env)
        self.assertEqual(b'dumb', env[b'TERM'])
        self.assertEqual('dumb', env['TERM'])
        self.assertEqual('1', env['CLICOLOR_FORCE'])

    @patch.dict(os.environ, {'TERM': 'dumb'}, clear=True)
    def test_get_environment_upgrades_host_dumb_term(self):
        env = self.handler.get_environment(self._work_request(None))
        self.assertEqual('xterm-256color', env['TERM'])
        self.assertEqual('1', env['FORCE_COLOR'])

    @patch.dict(os.environ, {}, clear=True)
    def test_get_environment_respects_bytes_no_color(self):
        env = self.handler.get_environment(self._work_request({'NO_COLOR': '1'}))
        self.assertNotIn('FORCE_COLOR', env)
        self.assertNotIn(b'FORCE_COLOR', env)
        self.assertEqual(b'1', env[b'NO_COLOR'])

    
