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
from rapid.testmapper import PythonFile
from tests.framework.unit_test import UnitTest


class TestQaDal(UnitTest):

    def test_parse_action(self):
        python_file = PythonFile(None, None)

        self.assertEqual("unit", python_file.parse_action("@rapid-unit Test:Test:Testing"))
        self.assertEqual("unit", python_file.parse_action("rapid-unit: Test:Test:Testing"))
        self.assertEqual(None, python_file.parse_action("@@@@rapid-unit12: Test:Test:Testing"))
