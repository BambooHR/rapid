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
from unittest import TestCase

from nose.tools import eq_, ok_

from rapid.master.data.database.dal.GeneralDal import GeneralDal
from rapid.workflow.data.models import Status


class TestGeneralDal(TestCase):

    def test_get_instance_with_attributes(self):
        dal = GeneralDal()
        instance = dal.get_instance(Status, {'type': "WHOOOHOOO"})

        eq_("WHOOOHOOO", instance.type, "object attribute was not set correctly.")

    def test_get_instance_with_no_attributes(self):
        dal = GeneralDal()
        instance = dal.get_instance(Status, {})

        eq_(None, instance.type, "object attribute was not set correctly.")

    def test_get_instance_with_none_attributes(self):
        dal = GeneralDal()
        instance = dal.get_instance(Status, None)

        eq_(None, instance.type, "object attribute was not set correctly.")

    def test_set_attribute_on_object(self):
        dal = GeneralDal()
        instance = Status()

        dal._set_attributes(instance, {"type": "Worked!"})

        eq_("Worked!", instance.type, "setting the attribute didn't work.")

    def test_set_invalid_attribute_on_object(self):
        dal = GeneralDal()
        instance = Status()

        dal._set_attributes(instance, {"foo": "No Worky!"})

        ok_(not hasattr(instance, 'foo'))
