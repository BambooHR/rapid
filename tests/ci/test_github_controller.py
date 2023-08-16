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

from rapid.ci.vcs.github_controller import GithubController
from tests.framework.unit_test import UnitTest


class TestGithubController(UnitTest):

    def test_get_json_value(self):
        mock_config = MagicMock()
        controller = GithubController(MagicMock(), MagicMock(), mock_config, MagicMock())

        self.assertEqual('something', controller._get_json_value({'test': {'trial': {'value': 'something'}}}, 'test.trial.value'))

    def test_process_webhooks_wraps_properly(self):
        controller = GithubController(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        self.assertEqual('wrapped_json_response', controller.process_webhooks.__func__.__name__)

    def test_process_webhooks_pipeline_wraps_properly(self):
        controller = GithubController(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        self.assertEqual('wrapped_json_response', controller.process_webhooks_pipeline.__func__.__name__)
