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
from unittest.mock import MagicMock, call

from ddt import ddt, data, unpack
from mock.mock import patch, Mock
from sqlalchemy import Boolean

from rapid.lib.exceptions import InvalidObjectException
from rapid.lib.constants import StatusConstants
from rapid.workflow.action_dal import ActionDal
from rapid.workflow.data.models import ActionInstance, PipelineParameters, PipelineInstance, ActionInstanceConfig, AppConfiguration
from tests.framework.unit_test import UnitTest


@ddt
class TestActionDal(UnitTest):

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

        self.assertEqual([AppConfiguration, ActionInstance, PipelineParameters, ActionInstanceConfig, ActionInstance, PipelineParameters, ActionInstanceConfig], session.query_args)

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

        self.assertTrue(PipelineParameters in session.outerjoin_args)
        self.assertEqual(PipelineParameters.__table__.columns['pipeline_instance_id'], session.outerjoin_args[1].left)
        self.assertEqual(ActionInstance.__table__.columns['pipeline_instance_id'], session.outerjoin_args[1].right)

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

        self.assertEqual(8, len(session.filter_args))

        filter_1 = session.filter_args[0]
        filter_2 = session.filter_args[1]
        filter_3 = session.filter_args[2]
        filter_4 = session.filter_args[3]
        filter_5 = session.filter_args[4]
        filter_6 = session.filter_args[5]
        filter_7 = session.filter_args[6]
        filter_8 = session.filter_args[7]

        self.assertEqual(ActionInstance.__table__.columns['status_id'], filter_1.left)
        self.assertEqual(StatusConstants.READY, filter_1.right.value)

        self.assertEqual(ActionInstance.__table__.columns['manual'], filter_2.left)
        self.assertEqual(0, filter_2.right.value)

        self.assertEqual(ActionInstance.__table__.columns['pipeline_instance_id'], filter_3.left)
        self.assertEqual(PipelineInstance.__table__.columns['id'], filter_3.right)

        self.assertEqual(PipelineInstance.__table__.columns['status_id'], filter_4.left)
        self.assertEqual(StatusConstants.INPROGRESS, filter_4.right.value)

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

        self.assertEqual(PipelineInstance.__table__.columns['priority'], session.order_by_args[0].element)
        self.assertEqual(PipelineInstance.__table__.columns['created_date'], session.order_by_args[1].element)
        self.assertEqual(PipelineInstance.__table__.columns['id'], session.order_by_args[2].element)
        self.assertEqual(ActionInstance.__table__.columns['order'], session.order_by_args[3].element)
        self.assertEqual(ActionInstance.__table__.columns['slice'], session.order_by_args[4].element)

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
        self.assertEqual(1, len(work_requests))
        self.assertEqual(1, work_request.action_instance_id)
        self.assertEqual(1, work_request.pipeline_instance_id)
        self.assertEqual(1, work_request.workflow_instance_id)

        self.assertEqual({"foo": "bar", "foo2": "bar2"}, work_request.environment)

    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_verify_working_verify_join(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_dal.get_verify_working(10)

        self.assertEqual(PipelineInstance, session.join_args[0])
        # self.assertEqual(StatusConstants.INPROGRESS, session.join_args[1].right.value)

    @patch('rapid.workflow.data.models.Base')
    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_verify_working_verify_filter_args(self, get_db_session, base):
        action_dal = ActionDal()

        now = datetime.datetime.utcnow()
        diff = now - datetime.timedelta(minutes=10)

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_dal.get_verify_working(10)

        self.assertEqual(6, len(session.filter_args))

        filter_1 = session.filter_args[0]
        filter_2 = session.filter_args[1]
        filter_3 = session.filter_args[2]
        filter_4 = session.filter_args[3]
        filter_5 = session.filter_args[4]
        filter_6 = session.filter_args[5]

        self.assertEqual(PipelineInstance.__table__.columns['status_id'], filter_1.left)
        self.assertEqual(StatusConstants.INPROGRESS, filter_1.right.value)

        self.assertEqual(ActionInstance.__table__.columns['status_id'], filter_2.left)
        self.assertEqual(StatusConstants.INPROGRESS, filter_2.right.value)

        self.assertEqual(ActionInstance.__table__.columns['assigned_to'], filter_3.left)
        self.assertEqual('', filter_3.right.value)

        self.assertEqual(ActionInstance.__table__.columns['start_date'], filter_4.left)
        self.assertEqual(diff.minute, filter_4.right.value.minute)
        self.assertEqual(diff.day, filter_4.right.value.day)
        self.assertEqual(diff.year, filter_4.right.value.year)
        self.assertEqual(diff.hour, filter_4.right.value.hour)

        self.assertEqual(ActionInstance.__table__.columns['end_date'], filter_5.left)
        self.assertEqual(Boolean, type(filter_5.type))

        self.assertEqual(ActionInstance.__table__.columns['manual'], filter_6.left)
        self.assertEqual(0, filter_6.right.value)

    @patch('rapid.workflow.action_dal.get_db_session')
    def test_get_verify_working_verify_results(self, get_db_session):
        action_dal = ActionDal()

        session = WrapperHelper()
        get_db_session.return_value = [session]

        action_instance = Mock(id=1, pipeline_instance_id=1)
        session.results.append(action_instance)

        results = action_dal.get_verify_working(10)

        self.assertEqual([action_instance.serialize()], results)

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

        self.assertEqual(404, exception.exception.code)
        self.assertEqual("Action Instance not found", exception.exception.description)

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

        self.assertEqual("Action Instance has been canceled.", action_dal.cancel_action_instance(123455)['message'])

        mock_workflow.complete_an_action.assert_called_with(123455, StatusConstants.CANCELED)
        mock_constants.cancel_worker.assert_called_with(get_action_instance().serialize())

    @data(StatusConstants.SUCCESS, StatusConstants.CANCELED)
    @patch('rapid.workflow.action_dal.ActionDal.get_action_instance_by_id')
    @patch('rapid.workflow.action_dal.get_db_session')
    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    def test_cancel_action_instance_leaves_finished_instance_unchanged(self, status_id, workflow_engine, db_session, get_action_instance):
        result, session, queue_constants = self._cancel(db_session, get_action_instance, status_id, True)

        self.assertEqual('already_finished', result['outcome'])
        workflow_engine.assert_not_called()
        queue_constants.cancel_worker.assert_not_called()
        session.commit.assert_not_called()

    @data((True, 'requested'), (False, 'worker_stop_failed'))
    @unpack
    @patch('rapid.workflow.action_dal.ActionDal.get_action_instance_by_id')
    @patch('rapid.workflow.action_dal.get_db_session')
    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    def test_cancel_action_instance_reports_running_worker_stop(self, worker_stopped, outcome, workflow_engine, db_session, get_action_instance):
        result, session, _ = self._cancel(db_session, get_action_instance, StatusConstants.INPROGRESS, worker_stopped)

        self.assertEqual(outcome, result['outcome'])
        workflow_engine.return_value.complete_an_action.assert_called_once_with(12, StatusConstants.CANCELED)
        session.commit.assert_called_once_with()

    @patch('rapid.workflow.action_dal.ActionDal.get_action_instance_by_id')
    @patch('rapid.workflow.action_dal.get_db_session')
    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    def test_cancel_action_instance_cancels_unassigned_ready_instance(self, workflow_engine, db_session, get_action_instance):
        result, session, _ = self._cancel(db_session, get_action_instance, StatusConstants.READY, False)

        self.assertEqual('requested', result['outcome'])
        workflow_engine.return_value.complete_an_action.assert_called_once_with(12, StatusConstants.CANCELED)
        session.commit.assert_called_once_with()

    @staticmethod
    def _cancel(db_session, get_action_instance, status_id, worker_stopped):
        session = Mock()
        db_session.return_value = [session]
        get_action_instance.return_value = Mock(status_id=status_id)
        queue_constants = Mock()
        queue_constants.cancel_worker.return_value = worker_stopped

        result = ActionDal(flask_app=Mock(), queue_constants=queue_constants).cancel_action_instance(12)
        return result, session, queue_constants

    @patch('rapid.workflow.action_dal.get_db_session')
    @patch('rapid.workflow.action_dal.ActionInstance')
    @patch.object(ActionDal, ActionDal._get_loaded_pipeline_instance.__name__)
    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    def test_reset_action_instance_contract(self, mock_instance_engine,
                                            mock_loaded_pipeline_instance,
                                            mock_action_instance,
                                            mock_get_session):
        mock_engine = Mock()
        mock_session = Mock()
        mock_get_session.return_value = [mock_session]
        mock_instance = Mock(status_id=StatusConstants.INPROGRESS)
        mock_pi_instance = Mock(action_instances=[mock_instance])

        mock_session.query().with_for_update().filter().first.return_value = mock_instance
        mock_loaded_pipeline_instance.return_value = mock_pi_instance
        mock_instance_engine.return_value = mock_engine

        dal = ActionDal()

        dal.reset_action_instance(11)

        mock_session.query.assert_called_with(mock_action_instance)
        mock_session.commit.assert_called_with()
        
        mock_loaded_pipeline_instance.assert_called_with(mock_session, mock_instance)
        mock_instance_engine.assert_called_with(dal.status_dal, mock_pi_instance)

    @patch('rapid.workflow.action_dal.PipelineInstance')
    @patch('rapid.workflow.action_dal.StageInstance')
    @patch('rapid.workflow.action_dal.WorkflowInstance')
    @patch('rapid.workflow.action_dal.joinedload')
    def test_get_loaded_pipeline_instance_contract(self, mock_load,
                                                   mock_workflow,
                                                   mock_stage,
                                                   mock_pipeline):
        mock_session = Mock()
        mock_action_instance = Mock()

        mock_load_second = Mock()
        mock_load_second.joinedload().joinedload.return_value = 'foobie'
        mock_load.side_effect = ['foobar', mock_load_second]

        dal = ActionDal()

        dal._get_loaded_pipeline_instance(mock_session, mock_action_instance)

        mock_session.query.assert_called_with(mock_pipeline)

        mock_load_second.joinedload.assert_called_with(mock_stage.workflow_instances)
        mock_load_second.joinedload().joinedload.assert_called_with(mock_workflow.action_instances)

        mock_session.query().options.assert_called_with('foobar', 'foobie')
        mock_session.query().options().get.assert_called_with(mock_action_instance.pipeline_instance_id)

    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    @patch('rapid.workflow.action_dal.get_db_session')
    def test_reset_single_action_instance_resets_target_and_qa_results_in_one_commit(self, get_db_session, workflow_engine):
        action_instance = self._finished_action_instance()
        session = self._locked_session(get_db_session, action_instance)
        workflow_engine.return_value.reset_single_action_instance.return_value = [12]
        qa_module = Mock()
        qa_module.reset_results.side_effect = lambda *args, **kwargs: session.commit.assert_not_called()
        dal = ActionDal(qa_module=qa_module, status_dal=Mock())

        self.assertEqual({"action_instance_id": 12, "outcome": "reset"}, dal.reset_action_instance(12, reset_single_slice=True))

        workflow_engine.assert_called_once_with(dal.status_dal, action_instance.pipeline_instance)
        workflow_engine.return_value.reset_single_action_instance.assert_called_once_with(action_instance)
        qa_module.reset_results.assert_called_once_with(12, session, commit=False)
        session.commit.assert_called_once_with()

    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    @patch('rapid.workflow.action_dal.get_db_session')
    def test_reset_single_action_instance_returns_false_when_not_found(self, get_db_session, workflow_engine):
        self._assert_reset_single_rejected(get_db_session, workflow_engine, None)

    @data(StatusConstants.READY, StatusConstants.INPROGRESS)
    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    @patch('rapid.workflow.action_dal.get_db_session')
    def test_reset_single_action_instance_rejects_unfinished_instance(self, status_id, get_db_session, workflow_engine):
        action_instance = self._finished_action_instance()
        action_instance.status_id = status_id

        self._assert_reset_single_rejected(get_db_session, workflow_engine, action_instance)

    @data(datetime.timedelta(days=3), datetime.timedelta(days=30), None)
    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    @patch('rapid.workflow.action_dal.get_db_session')
    def test_reset_single_action_instance_rejects_expired_or_unknown_age(self, pipeline_age, get_db_session, workflow_engine):
        action_instance = self._finished_action_instance()
        action_instance.pipeline_instance.created_date = None if pipeline_age is None else datetime.datetime.utcnow() - pipeline_age
        self._assert_reset_single_rejected(get_db_session, workflow_engine, action_instance)

    @patch('rapid.workflow.action_dal.InstanceWorkflowEngine')
    @patch('rapid.workflow.action_dal.get_db_session')
    def test_reset_single_action_instance_does_not_commit_when_qa_cleanup_fails(self, get_db_session, workflow_engine):
        session = self._locked_session(get_db_session, self._finished_action_instance())
        qa_module = Mock()
        workflow_engine.return_value.reset_single_action_instance.return_value = [12]
        qa_module.reset_results.side_effect = Exception("QA cleanup failed")

        with self.assertRaises(Exception):
            ActionDal(qa_module=qa_module, status_dal=Mock()).reset_action_instance(12, reset_single_slice=True)

        session.commit.assert_not_called()

    def _assert_reset_single_rejected(self, get_db_session, workflow_engine, action_instance):
        session = self._locked_session(get_db_session, action_instance)
        qa_module = Mock()

        self.assertFalse(ActionDal(qa_module=qa_module, status_dal=Mock()).reset_action_instance(12, reset_single_slice=True))
        workflow_engine.assert_not_called()
        qa_module.reset_results.assert_not_called()
        session.commit.assert_not_called()

    @staticmethod
    def _locked_session(get_db_session, action_instance):
        session = Mock()
        session.query.return_value.with_for_update.return_value.filter.return_value.first.return_value = action_instance
        session.query.return_value.options.return_value.get.return_value = action_instance.pipeline_instance if action_instance else None
        get_db_session.return_value = [session]
        return session

    @staticmethod
    def _finished_action_instance():
        return Mock(id=12, status_id=StatusConstants.FAILED, pipeline_instance=Mock(created_date=datetime.datetime.utcnow()))







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
