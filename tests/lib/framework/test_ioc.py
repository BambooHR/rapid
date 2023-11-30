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
from unittest.mock import Mock

from mock.mock import patch

from rapid.lib.framework.ioc import IOC
from rapid.lib.framework.injectable import Injectable
from tests.framework.unit_test import UnitTest


class NoCacheAllowed:
    ...

class TrialClass(object):

    def has_trial(self):
        return False


class OtherClass(NoCacheAllowed):

    def has_something(self):
        return True


class TestClass(Injectable):

    def __init__(self, trial: TrialClass, other: OtherClass, oneMore):
        self.trial = trial
        self.other = other
        self.oneMore = oneMore


class TestIOC(UnitTest):
    def setUp(self) -> None:
        self.setup_ioc()
        self.ioc = IOC.get_instance()

    def tearDown(self):
        self.teardown_ioc()

    def test_multi_dependency(self):
        testclass = IOC.get_class_instance(TestClass, "Something")

        self.assertEqual(False, testclass.trial.has_trial())

    def test_override_on_class(self):
        IOC.override('foobar', 'something')
        self.assertEqual('something', self.ioc._overrides['foobar'])
        self.assertEqual('something', IOC._overrides['foobar'])

    def test_is_injectable_from_injectable(self):
        self.assertTrue(self.ioc.is_injectable(TestClass))

    @patch('rapid.lib.framework.ioc.issubclass')
    def test_is_injectable_not_injectable(self, mock_sub):
        IOC._injectable = None
        self.ioc._injectable = None

        self.assertFalse(self.ioc.is_injectable(Mock))
        mock_sub.assert_not_called()

    def test_cache_value_cache_is_None_no_cache_or_error(self):
        self.ioc._cache = None
        self.ioc._cache_value('foobar', TestClass(Mock(), Mock(), Mock()))
        self.assertEqual(None, self.ioc._cache)

    def test_cache_value_ensure_cacheable_set(self):
        self.ioc._no_cacheable = None
        self.ioc.is_cached = True
        self.ioc._cache_value('foobar', TestClass(Mock(), Mock(), Mock()))
        self.assertEqual({}, self.ioc._cache)

    def test_cache_value_ensure_no_cacheable_not_cached(self):
        self.ioc.is_cached = True
        self.ioc.set_no_cacheable(NoCacheAllowed)

        self.ioc._cache_value('foobar', OtherClass())
        self.assertEqual({}, self.ioc._cache)

    def test_cache_value_works(self):
        self.ioc.is_cached = True
        self.ioc.set_no_cacheable(NoCacheAllowed)
        
        other = TrialClass()
        self.ioc._cache_value('foobar', other)
        self.assertEqual(other, self.ioc._cache['foobar'])
