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

import datetime
from unittest.case import TestCase
from unittest.mock import MagicMock

from mock.mock import patch, Mock
from nose.tools.trivial import eq_, ok_
from sqlalchemy import Boolean

from rapid.lib.exceptions import InvalidObjectException
from rapid.lib.constants import StatusConstants
from rapid.workflow.action_dal import ActionDal
from rapid.workflow.data.models import ActionInstance, PipelineParameters, PipelineInstance, ActionInstanceConfig, AppConfiguration


class TestActionDal(TestCase):

    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_workable_work_requests_verify_queryables(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance()
        pipeline_parameters = PipelineParameters()
        action_instance_config = ActionInstanceConfig()
        session.results.append((action_instance, pipeline_parameters, action_instance_config))

        action_dal.get_workable_work_requests()

        eq_([AppConfiguration, ActionInstance, PipelineParameters, ActionInstanceConfig, ActionInstance, PipelineParameters, ActionInstanceConfig], session.query_args)

    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_workable_work_requests_verify_outerjoin(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance()
        pipeline_parameters = PipelineParameters()
        action_instance_config = ActionInstanceConfig()
        session.results.append((action_instance, pipeline_parameters, action_instance_config))

        action_dal.get_workable_work_requests()

        ok_(PipelineParameters in session.outerjoin_args)
        eq_(PipelineParameters.__table__.columns['pipeline_instance_id'], session.outerjoin_args[1].left)
        eq_(ActionInstance.__table__.columns['pipeline_instance_id'], session.outerjoin_args[1].right)

    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_workable_work_requests_verify_filters(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = Mock()
        action_instance.serialize.return_value = {}
        pipeline_parameters = Mock()
        action_configs = Mock()
        session.results.append((action_instance, pipeline_parameters, action_configs))

        action_dal.get_workable_work_requests()

        eq_(8, len(session.filter_args))

        filter_1 = session.filter_args[0]
        filter_2 = session.filter_args[1]
        filter_3 = session.filter_args[2]
        filter_4 = session.filter_args[3]
        filter_5 = session.filter_args[4]
        filter_6 = session.filter_args[5]
        filter_7 = session.filter_args[6]
        filter_8 = session.filter_args[7]

        eq_(ActionInstance.__table__.columns['status_id'], filter_1.left)
        eq_(StatusConstants.READY, filter_1.right.value)

        eq_(ActionInstance.__table__.columns['manual'], filter_2.left)
        eq_(0, filter_2.right.value)

        eq_(ActionInstance.__table__.columns['pipeline_instance_id'], filter_3.left)
        eq_(PipelineInstance.__table__.columns['id'], filter_3.right)

        eq_(PipelineInstance.__table__.columns['status_id'], filter_4.left)
        eq_(StatusConstants.INPROGRESS, filter_4.right.value)

    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_workable_work_requests_verify_order_by(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance()
        pipeline_parameters = PipelineParameters()
        action_instance_config = ActionInstanceConfig()
        session.results.append((action_instance, pipeline_parameters, action_instance_config))

        action_dal.get_workable_work_requests()

        eq_(PipelineInstance.__table__.columns['priority'], session.order_by_args[0].element)
        eq_(PipelineInstance.__table__.columns['created_date'], session.order_by_args[1].element)
        eq_(PipelineInstance.__table__.columns['id'], session.order_by_args[2].element)
        eq_(ActionInstance.__table__.columns['order'], session.order_by_args[3].element)
        eq_(ActionInstance.__table__.columns['slice'], session.order_by_args[4].element)

    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_workable_work_requests_work_request_validation(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance(id=1, pipeline_instance_id=1, workflow_instance_id=1)
        pipeline_parameters = PipelineParameters(parameter="foo", value="bar")
        action_instance_config = ActionInstanceConfig()
        pipeline_parameters_2 = PipelineParameters(parameter="foo2", value="bar2")
        action_instance_config2 = ActionInstanceConfig()
        session.results.append((action_instance, pipeline_parameters, action_instance_config))
        session.results.append((action_instance, pipeline_parameters_2, action_instance_config2))

        work_requests = action_dal.get_workable_work_requests()
        work_request = work_requests[0]
        eq_(1, len(work_requests))
        eq_(1, work_request.action_instance_id)
        eq_(1, work_request.pipeline_instance_id)
        eq_(1, work_request.workflow_instance_id)

        eq_({"foo": "bar", "foo2": "bar2"}, work_request.environment)

    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_verify_working_verify_join(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_dal.get_verify_working(10)

        eq_(PipelineInstance, session.join_args[0])
        # eq_(StatusConstants.INPROGRESS, session.join_args[1].right.value)

    @patch('rapid.workflow.data.models.Base')
    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_verify_working_verify_filter_args(self, get_db_session, base):
        action_dal = ActionDal()

        now = datetime.datetime.utcnow()
        diff = now - datetime.timedelta(minutes=10)

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_dal.get_verify_working(10)

        eq_(6, len(session.filter_args))

        filter_1 = session.filter_args[0]
        filter_2 = session.filter_args[1]
        filter_3 = session.filter_args[2]
        filter_4 = session.filter_args[3]
        filter_5 = session.filter_args[4]
        filter_6 = session.filter_args[5]

        eq_(PipelineInstance.__table__.columns['status_id'], filter_1.left)
        eq_(StatusConstants.INPROGRESS, filter_1.right.value)

        eq_(ActionInstance.__table__.columns['status_id'], filter_2.left)
        eq_(StatusConstants.INPROGRESS, filter_2.right.value)

        eq_(ActionInstance.__table__.columns['assigned_to'], filter_3.left)
        eq_('', filter_3.right.value)

        eq_(ActionInstance.__table__.columns['start_date'], filter_4.left)
        eq_(diff.minute, filter_4.right.value.minute)
        eq_(diff.day, filter_4.right.value.day)
        eq_(diff.year, filter_4.right.value.year)
        eq_(diff.hour, filter_4.right.value.hour)

        eq_(ActionInstance.__table__.columns['end_date'], filter_5.left)
        eq_(Boolean, type(filter_5.type))

        eq_(ActionInstance.__table__.columns['manual'], filter_6.left)
        eq_(0, filter_6.right.value)

    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_verify_working_verify_results(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = Mock(id=1, pipeline_instance_id=1)
        session.results.append(action_instance)

        results = action_dal.get_verify_working(10)

        eq_([action_instance.serialize()], results)

    @patch('rapid.workflow.action_dal.ActionDal.get_action_instance_by_id')
    @patch('rapid.workflow.action_dal.get_db_session')
    def test_action_instance_returns_404_when_not_found(self, db_session, get_action_instance):
        """
        @rapid-unit Workflow:Cancel Action Instance:Should return a 404 if not found
        :return:
        :rtype:
        """
        db_session.return_value = [Mock()]
        get_action_instance.return_value = None

        action_dal = ActionDal(flask_app=Mock())
        with self.assertRaises(InvalidObjectException) as exception:
            action_dal.cancel_action_instance(12345)

        eq_(404, exception.exception.code)
        eq_("Action Instance not found", exception.exception.description)

    @patch('rapid.workflow.action_dal.StoreService')
    @patch('rapid.workflow.action_dal.ActionDal.get_action_instance_by_id')
    @patch('rapid.workflow.action_dal.get_db_session')
    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    def test_action_instance_cancels_current_running_clients(self, workflow_engine, db_session, get_action_instance, store_service):
        """
        @rapid-unit Workflow:Cancel Action Instance:Should cancel active client
        :param db_session:
        :type db_session:
        :param get_action_instance:
        :type get_action_instance:
        :param store_service:
        :type store_service:
        :return:
        :rtype:
        """
        db_session.return_value = [Mock()]
        mock_workflow = Mock()
        workflow_engine.return_value = mock_workflow
        get_action_instance.return_value = Mock(assigned_to='12345', status_id=StatusConstants.INPROGRESS)
        setattr(get_action_instance, 'id', '54321')

        mock_constants = Mock()
        action_dal = ActionDal(flask_app=Mock(), queue_constants=mock_constants)

        eq_("Action Instance has been canceled.", action_dal.cancel_action_instance(123455)['message'])

        mock_workflow.complete_an_action.assert_called_with(123455, StatusConstants.CANCELED)
        mock_constants.cancel_worker.assert_called_with(get_action_instance().serialize())


class WrapperHelper(object):
    def __init__(self):
        self.filter_args = []
        self.order_by_args = []
        self.query_args = []
        self.outerjoin_args = []
        self.join_args = []
        self.results = []

    def join(self, *args):
        self.join_args += args
        return self

    def outerjoin(self, *args):
        self.outerjoin_args += args
        return self

    def query(self, *args):
        self.query_args += args
        return self

    def filter(self, *args):
        self.filter_args += args
        return self

    def order_by(self, *args):
        self.order_by_args += args
        return self

    def all(self):
        return self.results

    def get(self, number: int):
        return MagicMock(process_queue=True)
