import datetime
from unittest.mock import Mock, patch
import pytest
from rapid.lib.constants import StatusConstants
from rapid.workflow.action_dal import ActionDal
from tests.master.util import test_instance_workflow_engine as fixtures


def setup_dal(age=datetime.timedelta(hours=71), layout=('1:4',)):
    fixture = fixtures.TestInstanceWorkflowEngine()
    pipeline = fixture._build_pipeline_instance(list(layout), completed=True)
    for order, stage in enumerate(pipeline.stage_instances):
        stage.order = order
    pipeline.action_instances = [action for stage in pipeline.stage_instances for workflow in stage.workflow_instances
                                 for action in workflow.action_instances]
    pipeline.created_date = None if age is None else datetime.datetime.utcnow() - age
    actions = pipeline.stage_instances[0].workflow_instances[0].action_instances
    target = actions[2]
    session = Mock()
    session.query.return_value.get.return_value = target
    dal = ActionDal(qa_module=Mock(), status_dal=fixture._get_mocked_dal())
    dal._get_loaded_pipeline_instance = Mock(return_value=pipeline)
    return dal, session, target, actions


def reset_single(dal, session, target):
    with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
        return dal.reset_action_instance(target.id, reset_single_slice=True)


def test_single_retry_resets_only_target_and_its_qa_results():
    dal, session, target, actions = setup_dal()
    target.status_id = StatusConstants.FAILED

    assert reset_single(dal, session, target) is True

    assert target.status_id == StatusConstants.READY
    assert [action.status_id for action in actions if action is not target] == [StatusConstants.SUCCESS] * 3
    dal.qa_module.reset_results.assert_called_once_with(target.id, session)


@pytest.mark.parametrize('age', [None, datetime.timedelta(hours=72)])
def test_single_retry_rejects_expired_or_unknown_pipeline_age(age):
    dal, session, target, _ = setup_dal(age)
    assert reset_single(dal, session, target) is False
    session.commit.assert_not_called()
    dal.qa_module.reset_results.assert_not_called()


def test_single_retry_rejects_unfinished_target():
    dal, session, target, _ = setup_dal()
    target.status_id = StatusConstants.INPROGRESS
    assert reset_single(dal, session, target) is False
    session.commit.assert_not_called()


def test_single_retry_rejects_slice_followed_by_later_action():
    dal, session, target, actions = setup_dal(layout=('1:4,1',))
    actions[-1].status_id = StatusConstants.CANCELED
    assert reset_single(dal, session, target) is False
    session.commit.assert_not_called()
    assert target.status_id == StatusConstants.SUCCESS


def test_single_retry_rejects_slice_once_a_later_stage_exists():
    dal, session, target, _ = setup_dal(layout=('1:4', '1:1'))
    assert reset_single(dal, session, target) is False
    session.commit.assert_not_called()
    assert target.status_id == StatusConstants.SUCCESS


@pytest.mark.parametrize('sibling_status, allowed', [(StatusConstants.READY, False), (StatusConstants.SUCCESS, True)])
def test_single_retry_on_canceled_pipeline_requires_no_leftover_work(sibling_status, allowed):
    dal, session, target, actions = setup_dal()
    target.status_id = StatusConstants.CANCELED
    dal._get_loaded_pipeline_instance.return_value.status_id = StatusConstants.CANCELED
    actions[0].status_id = sibling_status
    assert reset_single(dal, session, target) is allowed


@pytest.mark.parametrize('slice_value', [None, '1/1', 'bad', '1/x', '0/4', '5/4'])
def test_single_retry_rejects_non_grouped_or_invalid_slice(slice_value):
    dal, session, target, _ = setup_dal()
    target.slice = slice_value
    assert reset_single(dal, session, target) is False
    session.commit.assert_not_called()
    dal.qa_module.reset_results.assert_not_called()
    assert target.status_id == StatusConstants.SUCCESS
