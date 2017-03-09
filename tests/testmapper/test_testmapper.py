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
from unittest.case import TestCase

from nose.tools.trivial import eq_

from rapid.testmapper import PythonFile


class TestTestMapper(TestCase):

    def test_handle_unit_with_colon(self):
        file = PythonFile(None, None)

        file.handle_unit("@rapid-unit: Area:Feature:Behavior point")

        eq_(file._current_settings, {file.AREA: 'Area', file.FEATURE: 'Feature', file.BP: 'Behavior point', 'level': 'unit'})

    def test_handle_unit_without_colon(self):
        file = PythonFile(None, None)

        file.handle_unit("@rapid-unit Area:Feature:Behavior point")

        eq_(file._current_settings, {file.AREA: 'Area', file.FEATURE: 'Feature', file.BP: 'Behavior point', 'level': 'unit'})

    def test_handle_integration_with_colon(self):
        file = PythonFile(None, None)

        file.handle_integration("@rapid-integration: Area:Feature:Behavior point")

        eq_(file._current_settings, {file.AREA: 'Area', file.FEATURE: 'Feature', file.BP: 'Behavior point', 'level': 'integration'})

    def test_handle_integration_without_colon(self):
        file = PythonFile(None, None)

        file.handle_integration("@rapid-integration Area:Feature:Behavior point")

        eq_(file._current_settings, {file.AREA: 'Area', file.FEATURE: 'Feature', file.BP: 'Behavior point', 'level': 'integration'})

    def test_handle_selenium_with_colon(self):
        file = PythonFile(None, None)

        file.handle_selenium("@rapid-selenium: Area:Feature:Behavior point")

        eq_(file._current_settings, {file.AREA: 'Area', file.FEATURE: 'Feature', file.BP: 'Behavior point', 'level': 'selenium'})

    def test_handle_selenium_without_colon(self):
        file = PythonFile(None, None)

        file.handle_selenium("@rapid-selenium Area:Feature:Behavior point")

        eq_(file._current_settings, {file.AREA: 'Area', file.FEATURE: 'Feature', file.BP: 'Behavior point', 'level': 'selenium'})

    def test_handle_tags_with_colon(self):
        file = PythonFile(None, None)

        file.handle_tags("@rapid-tags: This is a tag")

        eq_(file._current_settings, {'tags': ['This', 'is', 'a', 'tag']})

    def test_handle_tags_without_colon(self):
        file = PythonFile(None, None)

        file.handle_tags("@rapid-tags This is a tag")

        eq_(file._current_settings, {'tags': ['This', 'is', 'a', 'tag']})