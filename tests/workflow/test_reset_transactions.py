from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine, event, update
from sqlalchemy.dialects import mysql
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from rapid.lib.constants import StatusConstants
from rapid.workflow.action_dal import ActionDal
from rapid.workflow.data.models import ActionInstance, PipelineInstance, PipelineParameters, StageInstance, WorkflowInstance


@pytest.fixture
def session():
    database = create_engine('sqlite://')
    for model in (PipelineInstance, PipelineParameters, StageInstance, WorkflowInstance, ActionInstance):
        model.__table__.create(database)
    with Session(database, expire_on_commit=False) as session:
        pipeline = PipelineInstance(id=1, pipeline_id=1, status_id=StatusConstants.FAILED)
        stage = StageInstance(id=1, stage_id=1, status_id=StatusConstants.FAILED, pipeline_instance=pipeline)
        workflow = WorkflowInstance(id=1, workflow_id=1, status_id=StatusConstants.FAILED, stage_instance=stage)
        action = ActionInstance(id=12, action_id=1, cmd='test', executable='test', args='', pipeline_instance=pipeline, workflow_instance=workflow, status_id=StatusConstants.FAILED)
        session.add(pipeline)
        session.commit()
        yield session
    database.dispose()


def test_status_graph_refreshes_an_already_loaded_sibling(session):
    action = session.get(ActionInstance, 12)
    session.execute(update(ActionInstance).where(ActionInstance.id == 12).values(status_id=StatusConstants.READY),
                    execution_options={'synchronize_session': False})
    session.commit()
    assert action.status_id == StatusConstants.FAILED
    ActionDal()._get_loaded_pipeline_instance(session, action.pipeline_instance_id)
    assert action.status_id == StatusConstants.READY


def test_status_graph_locks_pipeline_row_before_locking_its_graph(session):
    statements = []
    event.listen(session, 'do_orm_execute', lambda execution: statements.append(
        str(execution.statement.compile(dialect=mysql.dialect()))))
    ActionDal()._get_loaded_pipeline_instance(session, 1)
    assert 'FOR UPDATE' in statements[0] and 'JOIN' not in statements[0]
    assert 'FOR UPDATE' in statements[1] and 'JOIN' in statements[1]


def test_reconciliation_rechecks_candidate_after_refresh(session):
    pipeline = session.get(PipelineInstance, 1)
    pipeline.status_id = StatusConstants.INPROGRESS
    session.commit()
    dal = ActionDal()
    load = dal._get_loaded_pipeline_instance

    def refresh(current_session, pipeline_id):
        current_session.execute(update(ActionInstance).where(ActionInstance.id == 12).values(status_id=StatusConstants.READY),
                                execution_options={'synchronize_session': False})
        current_session.commit()
        return load(current_session, pipeline_id)

    dal._get_loaded_pipeline_instance = refresh
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        dal.reconcile_pipeline_instances()
    session.refresh(pipeline)
    assert pipeline.status_id == StatusConstants.INPROGRESS
    assert pipeline.end_date is None


def test_completion_commits_statistics_before_status_calculation():
    session = Mock()
    dal = ActionDal(store_service=Mock())
    dal.get_action_instance_by_id = Mock(return_value=Mock())
    dal._save_statistics = Mock()
    dal._save_status_information = Mock(side_effect=lambda *args: session.commit.assert_called_once_with())
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        dal.complete_action_instance(12, {'status': 'SUCCESS'})


def test_failed_status_calculation_rolls_back_partial_changes():
    session = Mock()
    dal = ActionDal(store_service=Mock())
    dal.store_service.is_completing.return_value = False
    dal._save_status = Mock(side_effect=RuntimeError('failed calculation'))
    dal._save_status_information(Mock(), session, {})
    session.rollback.assert_called_once_with()


def test_database_failure_in_status_calculation_fails_completion_without_end_date():
    session = Mock()
    action_instance = Mock(end_date=None)
    dal = ActionDal(store_service=Mock())
    dal.store_service.is_completing.return_value = False
    dal.get_action_instance_by_id = Mock(return_value=action_instance)
    dal._save_statistics = Mock()
    dal._save_status = Mock(side_effect=OperationalError('SELECT', {}, Exception('deadlock')))
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]), pytest.raises(OperationalError):
        dal.complete_action_instance(12, {'status': 'SUCCESS'})
    assert action_instance.end_date is None
    session.rollback.assert_called_once_with()
    session.commit.assert_called_once_with()
    dal.store_service.clear_completing.assert_any_call(12)


@pytest.mark.parametrize('worker_raises', [False, True])
def test_cancel_commits_before_contacting_worker(worker_raises):
    session = Mock()
    target = Mock(status_id=StatusConstants.INPROGRESS, assigned_to='worker-12')
    dal = ActionDal(queue_constants=Mock())
    dal.get_action_instance_by_id = Mock(return_value=target)
    dal._get_loaded_pipeline_instance = Mock()

    def stop_worker(_):
        session.commit.assert_called_once_with()
        if worker_raises:
            raise RuntimeError('worker unavailable')
        return True

    dal.queue_constants.cancel_worker.side_effect = stop_worker
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]), patch('rapid.workflow.action_dal.InstanceWorkflowEngine'):
        assert dal.cancel_action_instance(12) == {"message": "Action Instance has been canceled."}
