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
from rapid.lib.framework.ioc import IOC
from rapid.lib.framework.injectable import Injectable
from tests.framework.unit_test import UnitTest


class TrialClass(object):

    def has_trial(self):
        return False


class OtherClass(object):

    def has_something(self):
        return True


class TestClass(Injectable):

    def __init__(self, trial: TrialClass, other: OtherClass, oneMore):
        self.trial = trial
        self.other = other
        self.oneMore = oneMore


class TestIOC(UnitTest):

    def test_multi_dependency(self):
        testclass = IOC.get_class_instance(TestClass, "Something")

        self.assertEqual(False, testclass.trial.has_trial())


