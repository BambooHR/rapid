import datetime
from unittest.mock import Mock, patch
import pytest
from rapid.lib.constants import StatusConstants
from rapid.workflow.action_dal import ActionDal
from tests.workflow.test_reset_scope import build


def setup_dal(age=datetime.timedelta(hours=71), layout=('1:4', '1:1')):
    engine, actions = build(list(layout))
    target = actions[2]
    target.slice = "3/4"
    target.pipeline_instance = engine.pipeline
    target.pipeline_instance.created_date = None if age is None else datetime.datetime.utcnow() - age
    session = Mock()
    session.query.return_value.get.return_value = target
    dal = ActionDal(qa_module=Mock(), status_dal=engine.status_dal)
    dal._get_loaded_pipeline_instance = Mock(return_value=engine.pipeline)
    return dal, session, target, actions


@pytest.mark.parametrize('age', [None, datetime.timedelta(hours=72)])
def test_single_retry_rejects_expired_or_unknown_pipeline_age(age):
    dal, session, target, _ = setup_dal(age)
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, reset_single_slice=True) is False
    session.commit.assert_not_called()
    dal.qa_module.reset_results.assert_not_called()


def test_single_retry_rejects_unfinished_target():
    dal, session, target, _ = setup_dal()
    target.status_id = StatusConstants.INPROGRESS
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, reset_single_slice=True) is False
    session.commit.assert_not_called()


def test_single_retry_rejects_slice_followed_by_later_action():
    dal, session, target, actions = setup_dal(layout=('1:4,1', '1:1'))
    actions[-1].status_id = StatusConstants.CANCELED
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, reset_single_slice=True) is False
    session.commit.assert_not_called()
    assert target.status_id == StatusConstants.SUCCESS


@pytest.mark.parametrize('other_action_status, allowed', [(StatusConstants.READY, False), (StatusConstants.SUCCESS, True)])
def test_single_retry_on_canceled_pipeline_requires_no_leftover_work(other_action_status, allowed):
    dal, session, target, _ = setup_dal()
    target.status_id = StatusConstants.CANCELED
    target.pipeline_instance.status_id = StatusConstants.CANCELED
    target.pipeline_instance.stage_instances[1].workflow_instances[0].action_instances[0].status_id = other_action_status
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        result = dal.reset_action_instance(target.id, reset_single_slice=True)
    assert result == ({'action_instance_id': target.id, 'outcome': 'reset'} if allowed else False)


def test_single_retry_clears_only_target_qa_before_one_commit():
    dal, session, target, actions = setup_dal()
    dal.qa_module.reset_results.side_effect = lambda *args, **kwargs: session.commit.assert_not_called()
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, reset_single_slice=True)['outcome'] == 'reset'
    dal.qa_module.reset_results.assert_called_once_with(target.id, session, commit=False)
    session.commit.assert_called_once_with()
    assert actions[0].status_id == StatusConstants.SUCCESS


def test_cleanup_failure_never_commits_reset():
    dal, session, target, _ = setup_dal()
    dal.qa_module.reset_results.side_effect = RuntimeError('cleanup failed')
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        with pytest.raises(RuntimeError):
            dal.reset_action_instance(target.id, reset_single_slice=True)
    session.commit.assert_not_called()


def test_worker_recovery_keeps_existing_workflow_reset_behavior():
    dal, session, target, actions = setup_dal(datetime.timedelta(days=4), layout=('1:4,1', '1:1'))
    target.status_id = StatusConstants.INPROGRESS
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, check_status=True) is True
    assert all(action.status_id == StatusConstants.NEW for action in actions)
    assert [call.args[0] for call in dal.qa_module.reset_results.call_args_list] == [action.id for action in actions]


def test_complete_reset_keeps_legacy_reset_selection():
    dal, session, target, actions = setup_dal(layout=('1:4,1', '1:1'))
    for action in actions:
        action.action_id = 100 if action.order == 0 else 200
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        dal.reset_action_instance(target.id, complete_reset=True)
    assert [call.args[0] for call in dal.qa_module.reset_results.call_args_list] == [action.id for action in actions[:4]]
    assert actions[-1].status_id == StatusConstants.SUCCESS


@pytest.mark.parametrize('slice_value', [None, '1/1', 'bad', '1/x', '0/4', '5/4'])
def test_single_retry_rejects_non_grouped_or_invalid_slice(slice_value):
    dal, session, target, _ = setup_dal()
    target.slice = slice_value
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        assert dal.reset_action_instance(target.id, reset_single_slice=True) is False
    session.commit.assert_not_called()
    dal.qa_module.reset_results.assert_not_called()
    assert target.status_id == StatusConstants.SUCCESS
