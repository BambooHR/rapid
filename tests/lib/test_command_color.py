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

from rapid.lib.command_color import apply_command_colors, apply_container_command_colors, command_color_entries
from tests.framework.unit_test import UnitTest


class TestCommandColor(UnitTest):

    def test_apply_command_colors_sets_tool_variables_and_term(self):
        env = {}
        apply_command_colors(env)
        self.assertEqual('1', env['FORCE_COLOR'])
        self.assertEqual('1', env['PY_COLORS'])
        self.assertEqual('1', env['CLICOLOR_FORCE'])
        self.assertEqual('xterm-256color', env['TERM'])

    def test_apply_command_colors_replaces_dumb_term(self):
        env = {'TERM': 'dumb'}
        apply_command_colors(env)
        self.assertEqual('xterm-256color', env['TERM'])

    def test_apply_command_colors_keeps_empty_term(self):
        env = {'TERM': ''}
        apply_command_colors(env)
        self.assertEqual('', env['TERM'])
        self.assertEqual('1', env['FORCE_COLOR'])

    def test_apply_command_colors_keeps_bytes_job_values(self):
        env = {b'FORCE_COLOR': b'0', b'TERM': b'dumb', 'PATH': '/bin'}
        apply_command_colors(env)
        self.assertNotIn('FORCE_COLOR', env)
        self.assertNotIn('TERM', env)
        self.assertEqual(b'0', env[b'FORCE_COLOR'])
        self.assertEqual(b'xterm-256color', env[b'TERM'])
        self.assertEqual('1', env['CLICOLOR_FORCE'])
        self.assertEqual('1', env['PY_COLORS'])

    def test_apply_command_colors_keeps_existing_values(self):
        env = {'FORCE_COLOR': '0', 'TERM': 'xterm-256color'}
        apply_command_colors(env)
        self.assertEqual('0', env['FORCE_COLOR'])
        self.assertEqual('xterm-256color', env['TERM'])
        self.assertEqual('1', env['CLICOLOR_FORCE'])
        self.assertEqual('1', env['PY_COLORS'])

    def test_apply_command_colors_respects_no_color(self):
        env = {'NO_COLOR': '1', 'TERM': 'dumb'}
        apply_command_colors(env)
        self.assertNotIn('FORCE_COLOR', env)
        self.assertNotIn('PY_COLORS', env)
        self.assertNotIn('CLICOLOR_FORCE', env)
        self.assertEqual('dumb', env['TERM'])

    def test_apply_command_colors_empty_no_color_is_unset(self):
        env = {'NO_COLOR': '', 'TERM': 'dumb'}
        apply_command_colors(env)
        self.assertEqual('1', env['FORCE_COLOR'])
        self.assertEqual('xterm-256color', env['TERM'])

    def test_apply_command_colors_respects_bytes_no_color(self):
        env = {b'NO_COLOR': b'1'}
        apply_command_colors(env)
        self.assertNotIn('FORCE_COLOR', env)

    def test_apply_command_colors_empty_bytes_no_color_is_unset(self):
        env = {b'NO_COLOR': b'', b'TERM': b'dumb'}
        apply_command_colors(env)
        self.assertEqual('1', env['FORCE_COLOR'])
        self.assertEqual(b'xterm-256color', env[b'TERM'])

    def test_apply_container_command_colors_leaves_missing_term(self):
        env = {}
        apply_container_command_colors(env)
        self.assertEqual('1', env['FORCE_COLOR'])
        self.assertEqual('1', env['PY_COLORS'])
        self.assertEqual('1', env['CLICOLOR_FORCE'])
        self.assertNotIn('TERM', env)

    def test_apply_container_command_colors_replaces_dumb_term(self):
        env = {'TERM': 'dumb'}
        apply_container_command_colors(env)
        self.assertEqual('xterm-256color', env['TERM'])

    def test_apply_container_command_colors_keeps_existing_term(self):
        env = {'TERM': 'screen'}
        apply_container_command_colors(env)
        self.assertEqual('screen', env['TERM'])

    def test_command_color_entries_for_containers(self):
        self.assertEqual(
            [
                {'name': 'FORCE_COLOR', 'value': '1'},
                {'name': 'PY_COLORS', 'value': '1'},
                {'name': 'CLICOLOR_FORCE', 'value': '1'},
            ],
            command_color_entries(None),
        )
        self.assertNotIn('TERM', [entry['name'] for entry in command_color_entries(None)])

    def test_command_color_entries_skip_values_the_job_set(self):
        entries = command_color_entries({'FORCE_COLOR': '0', 'TERM': 'screen'})
        names = [entry['name'] for entry in entries]
        self.assertNotIn('FORCE_COLOR', names)
        self.assertNotIn('TERM', names)
        self.assertIn('PY_COLORS', names)
        self.assertIn('CLICOLOR_FORCE', names)

    def test_command_color_entries_replaces_dumb_term(self):
        entries = command_color_entries({'TERM': 'dumb'})
        term = [entry for entry in entries if entry['name'] == 'TERM']
        self.assertEqual([{'name': 'TERM', 'value': 'xterm-256color'}], term)

    def test_command_color_entries_respect_no_color(self):
        self.assertEqual([], command_color_entries({'NO_COLOR': '1'}))

    def test_command_color_entries_empty_no_color_is_unset(self):
        names = [entry['name'] for entry in command_color_entries({'NO_COLOR': ''})]
        self.assertIn('FORCE_COLOR', names)
        self.assertNotIn('TERM', names)
