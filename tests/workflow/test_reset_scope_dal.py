import datetime
from unittest.mock import Mock, patch
import pytest
from rapid.lib.constants import StatusConstants as S
from rapid.workflow.action_dal import ActionDal
from tests.workflow.test_reset_scope import build


def setup_dal(age=datetime.timedelta(hours=71)):
    engine, actions = build(['1:4,1', '1:1'])
    target = actions[2]
    target.slice = "3/4"
    target.pipeline_instance = engine.pipeline
    target.pipeline_instance.created_date = None if age is None else datetime.datetime.utcnow() - age
    session = Mock()
    session.query.return_value.with_for_update.return_value.filter.return_value.first.return_value = target
    dal = ActionDal(qa_module=Mock(), status_dal=engine.status_dal)
    dal._get_loaded_pipeline_instance = Mock(return_value=engine.pipeline)
    return dal, session, target, actions


@pytest.mark.parametrize('age', [None, datetime.timedelta(hours=72), datetime.timedelta(days=30)])
def test_single_retry_rejects_expired_or_unknown_pipeline_age(age):
    dal, session, target, _ = setup_dal(age)
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, reset_single_slice=True) is False
    session.commit.assert_not_called()
    dal.qa_module.reset_results.assert_not_called()


@pytest.mark.parametrize('status', [S.NEW, S.READY, S.INPROGRESS])
def test_single_retry_rejects_unfinished_target(status):
    dal, session, target, _ = setup_dal()
    target.status_id = status
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, reset_single_slice=True) is False
    session.commit.assert_not_called()


def test_single_retry_clears_only_target_qa_before_one_commit():
    dal, session, target, actions = setup_dal()
    dal.qa_module.reset_results.side_effect = lambda *args, **kwargs: session.commit.assert_not_called()
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, reset_single_slice=True)['outcome'] == 'reset'
    dal.qa_module.reset_results.assert_called_once_with(target.id, session, commit=False)
    session.commit.assert_called_once_with()
    assert actions[0].status_id == S.SUCCESS


def test_cleanup_failure_never_commits_reset():
    dal, session, target, _ = setup_dal()
    dal.qa_module.reset_results.side_effect = RuntimeError('cleanup failed')
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        with pytest.raises(RuntimeError):
            dal.reset_action_instance(target.id, reset_single_slice=True)
    session.commit.assert_not_called()


def test_worker_recovery_keeps_existing_workflow_reset_behavior():
    dal, session, target, actions = setup_dal(datetime.timedelta(days=4))
    target.status_id = S.INPROGRESS
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, check_status=True) is True
    assert all(action.status_id == S.NEW for action in actions)
    assert [call.args[0] for call in dal.qa_module.reset_results.call_args_list] == [a.id for a in actions]


@pytest.mark.parametrize('complete_reset', [False, True])
def test_default_slice_option_keeps_legacy_reset_selection(complete_reset):
    dal, session, target, actions = setup_dal()
    for action in actions:
        action.action_id = 100 if action.order == 0 else 200
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        dal.reset_action_instance(target.id, complete_reset=complete_reset)
    expected = actions[:4] if complete_reset else actions
    assert [call.args[0] for call in dal.qa_module.reset_results.call_args_list] == [a.id for a in expected]
    if complete_reset:
        assert actions[-1].status_id == S.SUCCESS
    else:
        assert actions[-1].status_id == S.NEW


@pytest.mark.parametrize('slice_value', [None, '', '1/1', 'bad', '1/x', '1/2/3', '0/4', '5/4'])
def test_single_retry_rejects_non_grouped_or_invalid_slice(slice_value):
    dal, session, target, _ = setup_dal()
    target.slice = slice_value
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, reset_single_slice=True) is False
    session.commit.assert_not_called()
    dal.qa_module.reset_results.assert_not_called()
    assert target.status_id == S.SUCCESS


@pytest.mark.parametrize('second_stop', [True, False])
def test_cancel_retries_worker_stop_without_completing_action_again(second_stop):
    session = Mock()
    target = Mock(status_id=S.INPROGRESS, assigned_to='worker-12')
    queue = Mock()
    queue.cancel_worker.side_effect = [False, second_stop]
    dal = ActionDal(queue_constants=queue)
    dal.get_action_instance_by_id = Mock(return_value=target)
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]), patch('rapid.workflow.action_dal.InstanceWorkflowEngine') as engine:
        engine.return_value.complete_an_action.side_effect = lambda *args: setattr(target, 'status_id', S.CANCELED)
        assert dal.cancel_action_instance(12)['outcome'] == 'worker_stop_failed'
        assert dal.cancel_action_instance(12)['outcome'] == ('requested' if second_stop else 'worker_stop_failed')
        engine.return_value.complete_an_action.assert_called_once_with(12, S.CANCELED)
    assert queue.cancel_worker.call_count == 2
