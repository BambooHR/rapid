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

from rapid.master.data.database.dal.general_dal import GeneralDal
from tests.framework.unit_test import UnitTest


class TestGeneralDal(UnitTest):

    def test_get_instance_with_attributes(self):
        dal = GeneralDal()
        instance = dal.get_instance(TestStatus, {'type': "WHOOOHOOO"})

        self.assertEqual("WHOOOHOOO", instance.type, "object attribute was not set correctly.")

    def test_get_instance_with_no_attributes(self):
        dal = GeneralDal()
        instance = dal.get_instance(TestStatus, {})

        self.assertEqual(None, instance.type, "object attribute was not set correctly.")

    def test_get_instance_with_none_attributes(self):
        dal = GeneralDal()
        instance = dal.get_instance(TestStatus, None)

        self.assertEqual(None, instance.type, "object attribute was not set correctly.")

    def test_set_attribute_on_object(self):
        dal = GeneralDal()
        instance = TestStatus()

        dal._set_attributes(instance, {"type": "Worked!"})

        self.assertEqual("Worked!", instance.type, "setting the attribute didn't work.")

    def test_set_invalid_attribute_on_object(self):
        dal = GeneralDal()
        instance = TestStatus()

        dal._set_attributes(instance, {"foo": "No Worky!"})

        self.assertTrue(not hasattr(instance, 'foo'))


class TestStatus(object):
    type = None

    def __init__(self, type=None):
        self.type = type

