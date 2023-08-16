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
from mock import Mock
from mock.mock import patch

from rapid.lib.constants import ModuleConstants
from rapid.lib.framework.ioc import IOC
from rapid.lib import get_db_session
from rapid.master.data.database.dal import get_dal, setup_dals
from rapid.master.data.database.dal.general_dal import GeneralDal
from rapid.workflow.data.dal.pipeline_dal import PipelineDal
from rapid.workflow.data.models import *
from tests.framework.unit_test import UnitTest


class TestDalPackage(UnitTest):

    def test_setup_dals(self):
        mock_app = Mock()
        IOC.register_global(ModuleConstants.CI_MODULE, Mock())
        IOC.register_global('flask_app', mock_app)
        setup_dals(mock_app)

        for clazz in [Action, ActionInstance, Pipeline, PipelineInstance, PipelineParameters, PipelineStatistics, Stage,
                      StageInstance, Statistics, Status, Workflow, WorkflowInstance]:
            if Pipeline == clazz:
                self.assertEqual(PipelineDal, get_dal(clazz).__class__, clazz)
            else:
                self.assertEqual(GeneralDal, get_dal(clazz).__class__, clazz)

    def test_get_bogus_dal(self):
        self.assertEqual(None, get_dal("BogusClass"))

    @patch("rapid.lib.db")
    def test_get_db_session_if_None(self, db):
        db.session = None
        for session in get_db_session():
            self.assertEqual(None, session)

    @patch("rapid.lib.db")
    def test_get_db_session_if_not_none(self, db):
        db.session = Mock(id='trial')
        for session in get_db_session():
            self.assertEqual('trial', session.id)
        self.assertEqual(1, db.session.rollback.call_count)
        self.assertEqual(1, db.session.remove.call_count)
