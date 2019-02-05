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

from mock import Mock
from mock.mock import patch
from nose.tools.trivial import eq_

from rapid.lib.Constants import ModuleConstants
from rapid.lib.framework.IOC import IOC
from rapid.master.data.database import get_db_session
from rapid.master.data.database.dal import get_dal, setup_dals
from rapid.master.data.database.dal.general_dal import GeneralDal
from rapid.workflow.data.dal.PipelineDal import PipelineDal
from rapid.workflow.data.models import *


class TestDalPackage(TestCase):

    def test_setup_dals(self):
        mock_app = Mock()
        IOC.register_global(ModuleConstants.CI_MODULE, Mock())
        IOC.register_global('flask_app', mock_app)
        setup_dals(mock_app)

        for clazz in [Action, ActionInstance, Pipeline, PipelineInstance, PipelineParameters, PipelineStatistics, Stage,
                      StageInstance, Statistics, Status, Workflow, WorkflowInstance]:
            if Pipeline == clazz:
                eq_(PipelineDal, get_dal(clazz).__class__, clazz)
            else:
                eq_(GeneralDal, get_dal(clazz).__class__, clazz)

    def test_get_bogus_dal(self):
        eq_(None, get_dal("BogusClass"))

    @patch("rapid.master.data.database.db")
    def test_get_db_session_if_None(self, db):
        db.session = None
        for session in get_db_session():
            eq_(None, session)

    @patch("rapid.master.data.database.db")
    def test_get_db_session_if_not_none(self, db):
        db.session = Mock(id='trial')
        for session in get_db_session():
            eq_('trial', session.id)
        eq_(1, db.session.rollback.call_count)
        eq_(1, db.session.remove.call_count)
