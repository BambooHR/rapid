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

from mock.mock import patch, Mock
from nose.tools.trivial import eq_, ok_
from sqlalchemy.sql.sqltypes import NullType

from rapid.lib.Exceptions import InvalidObjectException
from rapid.lib.Constants import StatusConstants
from rapid.workflow.ActionDal import ActionDal
from rapid.workflow.data.models import ActionInstance, PipelineParameters, PipelineInstance


class TestActionDal(TestCase):

    @patch('rapid.workflow.ActionDal.get_db_session')
    def test_get_workable_work_requests_verify_queryables(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance()
        pipeline_parameters = PipelineParameters()
        session.results.append((action_instance, pipeline_parameters))

        action_dal.get_workable_work_requests()

        eq_([ActionInstance, PipelineParameters], session.query_args)

    @patch('rapid.workflow.ActionDal.get_db_session')
    def test_get_workable_work_requests_verify_outerjoin(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance()
        pipeline_parameters = PipelineParameters()
        session.results.append((action_instance, pipeline_parameters))

        action_dal.get_workable_work_requests()

        ok_(PipelineParameters in session.outerjoin_args)
        eq_(PipelineParameters.__table__.columns['pipeline_instance_id'], session.outerjoin_args[1].left)
        eq_(ActionInstance.__table__.columns['pipeline_instance_id'], session.outerjoin_args[1].right)

    @patch('rapid.workflow.ActionDal.get_db_session')
    def test_get_workable_work_requests_verify_filters(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance()
        pipeline_parameters = PipelineParameters()
        session.results.append((action_instance, pipeline_parameters))

        action_dal.get_workable_work_requests()

        eq_(4, len(session.filter_args))

        filter_1 = session.filter_args[0]
        filter_2 = session.filter_args[1]
        filter_3 = session.filter_args[2]
        filter_4 = session.filter_args[3]

        eq_(ActionInstance.__table__.columns['status_id'], filter_1.left)
        eq_(StatusConstants.READY, filter_1.right.value)

        eq_(ActionInstance.__table__.columns['manual'], filter_2.left)
        eq_(0, filter_2.right.value)

        eq_(ActionInstance.__table__.columns['pipeline_instance_id'], filter_3.left)
        eq_(PipelineInstance.__table__.columns['id'], filter_3.right)

        eq_(PipelineInstance.__table__.columns['status_id'], filter_4.left)
        eq_(StatusConstants.INPROGRESS, filter_4.right.value)

    @patch('rapid.workflow.ActionDal.get_db_session')
    def test_get_workable_work_requests_verify_order_by(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance()
        pipeline_parameters = PipelineParameters()
        session.results.append((action_instance, pipeline_parameters))

        action_dal.get_workable_work_requests()

        eq_(PipelineInstance.__table__.columns['priority'], session.order_by_args[0].element)
        eq_(PipelineInstance.__table__.columns['created_date'], session.order_by_args[1].element)
        eq_(PipelineInstance.__table__.columns['id'], session.order_by_args[2].element)
        eq_(ActionInstance.__table__.columns['order'], session.order_by_args[3].element)
        eq_(ActionInstance.__table__.columns['slice'], session.order_by_args[4].element)

    @patch('rapid.workflow.ActionDal.get_db_session')
    def test_get_workable_work_requests_work_request_validation(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance(id=1, pipeline_instance_id=1, workflow_instance_id=1)
        pipeline_parameters = PipelineParameters(parameter="foo", value="bar")
        pipeline_parameters_2 = PipelineParameters(parameter="foo2", value="bar2")
        session.results.append((action_instance, pipeline_parameters))
        session.results.append((action_instance, pipeline_parameters_2))

        work_requests = action_dal.get_workable_work_requests()
        work_request = work_requests[0]
        eq_(1, len(work_requests))
        eq_(1, work_request.action_instance_id)
        eq_(1, work_request.pipeline_instance_id)
        eq_(1, work_request.workflow_instance_id)

        eq_({"foo": "bar", "foo2": "bar2"}, work_request.environment)

    @patch('rapid.workflow.ActionDal.get_db_session')
    def test_get_verify_working_verify_join(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance()
        session.results.append(action_instance)

        action_dal.get_verify_working(10)

        eq_(PipelineInstance, session.join_args[0])
        # eq_(StatusConstants.INPROGRESS, session.join_args[1].right.value)

    @patch('rapid.workflow.ActionDal.get_db_session')
    def test_get_verify_working_verify_filter_args(self, get_db_session):
        action_dal = ActionDal()

        now = datetime.datetime.utcnow()
        diff = now - datetime.timedelta(minutes=10)

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance()
        session.results.append(action_instance)

        action_dal.get_verify_working(10)

        eq_(5, len(session.filter_args))

        filter_1 = session.filter_args[0]
        filter_2 = session.filter_args[1]
        filter_3 = session.filter_args[2]
        filter_4 = session.filter_args[3]
        filter_5 = session.filter_args[4]

        eq_(PipelineInstance.__table__.columns['status_id'], filter_1.left)
        eq_(StatusConstants.INPROGRESS, filter_1.right.value)

        eq_(ActionInstance.__table__.columns['status_id'], filter_2.left)
        eq_(StatusConstants.INPROGRESS, filter_2.right.value)

        eq_(ActionInstance.__table__.columns['start_date'], filter_3.left)
        eq_(diff.minute, filter_3.right.value.minute)
        eq_(diff.day, filter_3.right.value.day)
        eq_(diff.year, filter_3.right.value.year)
        eq_(diff.hour, filter_3.right.value.hour)

        eq_(ActionInstance.__table__.columns['end_date'], filter_4.left)
        eq_(NullType, type(filter_4.type))

        eq_(ActionInstance.__table__.columns['manual'], filter_5.left)
        eq_(0, filter_5.right.value)

    @patch('rapid.workflow.ActionDal.get_db_session')
    def test_get_verify_working_verify_results(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = ActionInstance(id=1, pipeline_instance_id=1)
        session.results.append(action_instance)

        results = action_dal.get_verify_working(10)

        eq_([action_instance.serialize()], results)

    @patch('rapid.workflow.ActionDal.ActionDal.get_action_instance_by_id')
    @patch('rapid.workflow.ActionDal.get_db_session')
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

    @patch('rapid.workflow.ActionDal.StoreService')
    @patch('rapid.workflow.ActionDal.ActionDal.get_action_instance_by_id')
    @patch('rapid.workflow.ActionDal.get_db_session')
    def test_action_instance_cancels_current_running_clients(self, db_session, get_action_instance, store_service):
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
        get_action_instance.return_value = Mock(assigned_to='12345', status_id=StatusConstants.INPROGRESS)

        client1 = Mock()
        client1.get_uri.return_value = '12345'

        client2 = Mock()
        store_service.get_clients.return_value = {"12345": client1, "54321": client2}

        action_dal = ActionDal(flask_app=Mock())

        eq_("Action Instance has been canceled.", action_dal.cancel_action_instance(123455)['message'])

        eq_(1, client1.cancel_work.call_count)
        eq_(0, client2.cancel_work.call_count)


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