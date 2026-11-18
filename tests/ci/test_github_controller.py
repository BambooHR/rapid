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
from mock.mock import MagicMock

from rapid.ci.vcs.github_controller import COMMIT_MESSAGE_LIMIT, GithubController
from tests.framework.unit_test import UnitTest


class TestGithubController(UnitTest):

    def test_get_json_value(self):
        mock_config = MagicMock()
        controller = GithubController(MagicMock(), MagicMock(), mock_config)

        self.assertEqual('something', controller._get_json_value({'test': {'trial': {'value': 'something'}}}, 'test.trial.value'))

    def test_process_webhooks_wraps_properly(self):
        controller = GithubController(MagicMock(), MagicMock(), MagicMock())

        self.assertEqual('wrapped_json_response', controller.process_webhooks.__func__.__name__)

    def test_process_webhooks_pipeline_wraps_properly(self):
        controller = GithubController(MagicMock(), MagicMock(), MagicMock())

        self.assertEqual('wrapped_json_response', controller.process_webhooks_pipeline.__func__.__name__)

    def _controller(self, default_parameters=None):
        config = MagicMock()
        config.github_default_parameters = default_parameters
        return GithubController(MagicMock(), config, MagicMock())

    def test_build_request_parameters_stores_commit_subject(self):
        controller = self._controller()

        parameters = controller._build_request_parameters({
            'ref': 'refs/heads/main',
            'head_commit': {'message': 'Fix the list\n\nMore detail'},
        })

        self.assertEqual('main', parameters['parameters']['branch'])
        self.assertEqual('Fix the list', parameters['parameters']['commit_message'])

    def test_build_request_parameters_caps_commit_subject(self):
        controller = self._controller()

        parameters = controller._build_request_parameters({
            'head_commit': {'message': 'x' * (COMMIT_MESSAGE_LIMIT + 1)},
        })

        self.assertEqual(COMMIT_MESSAGE_LIMIT, len(parameters['parameters']['commit_message']))

    def test_build_request_parameters_skips_a_missing_commit_message(self):
        controller = self._controller()

        parameters = controller._build_request_parameters({'head_commit': None, 'ref': 'refs/heads/main'})

        self.assertNotIn('commit_message', parameters['parameters'])

    def test_build_request_parameters_uses_the_first_nonempty_line(self):
        controller = self._controller()

        parameters = controller._build_request_parameters({
            'head_commit': {'message': '\n\nReal subject\nbody'},
        })

        self.assertEqual('Real subject', parameters['parameters']['commit_message'])

    def test_build_request_parameters_drops_emoji_and_shell_characters(self):
        controller = self._controller()

        parameters = controller._build_request_parameters({
            'head_commit': {'message': 'Ship it 🚀; rm -rf / `curl evil`'},
        })

        self.assertEqual('Ship it rm -rf / curl evil', parameters['parameters']['commit_message'])
        self.assertNotIn('🚀', parameters['parameters']['commit_message'])

    def test_build_request_parameters_keeps_a_configured_commit_message(self):
        controller = self._controller('commit_message:sender.login')

        parameters = controller._build_request_parameters({
            'sender': {'login': 'octocat'},
            'head_commit': {'message': 'Fix the list\n\nbody'},
        })

        self.assertEqual('octocat', parameters['parameters']['commit_message'])

    def test_build_request_parameters_makes_a_configured_message_safe(self):
        controller = self._controller('commit_message:head_commit.message')

        parameters = controller._build_request_parameters({
            'head_commit': {'message': '\n\nSubject $(reboot) 🎉\n\nbody'},
        })

        self.assertEqual('Subject reboot', parameters['parameters']['commit_message'])
        self.assertLessEqual(len(parameters['parameters']['commit_message']), COMMIT_MESSAGE_LIMIT)
