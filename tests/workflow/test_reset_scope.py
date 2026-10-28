import pytest
from rapid.lib.constants import StatusConstants as S
from rapid.workflow.workflow_engine import InstanceWorkflowEngine
from tests.master.util import test_instance_workflow_engine as fixtures


def build(layout):
    fixture = fixtures.TestInstanceWorkflowEngine()
    pipeline = fixture._build_pipeline_instance(layout, completed=True)
    pipeline.id = 4311
    for i, stage in enumerate(pipeline.stage_instances):
        stage.order = i
        stage.stage_id = stage.id
    engine = InstanceWorkflowEngine(fixture._get_mocked_dal(), pipeline)
    return engine, pipeline.stage_instances[0].workflow_instances[0].action_instances


def test_single_slice_resets_only_third_slice():
    engine, actions = build(['1:4,1', '1:1'])
    before = [fixtures.TestInstanceWorkflowEngine._instance_state(a) for a in actions]
    assert engine.reset_single_action_instance(actions[2]) == [actions[2].id]
    assert actions[2].status_id == S.READY
    assert actions[2].isolated_retry is True
    for i in (0, 1, 3, 4):
        assert fixtures.TestInstanceWorkflowEngine._instance_state(actions[i]) == before[i]


def test_legacy_false_resets_entire_workflow_including_later_orders():
    engine, actions = build(['1:1,4,1', '1:1'])
    actions[2].isolated_retry = True
    assert engine.reset_action(actions[2], complete_reset=False) == [a.id for a in actions]
    assert all(a.status_id == S.NEW and a.isolated_retry is False for a in actions)
    assert engine.pipeline.stage_instances[1].status_id == S.SUCCESS


@pytest.mark.parametrize('outcome', [S.SUCCESS, S.FAILED, S.CANCELED])
def test_isolated_completion_does_not_change_other_actions_or_stages(outcome):
    engine, actions = build(['1:4,1', '1:1'])
    actions[-1].status_id = S.NEW
    before = fixtures.TestInstanceWorkflowEngine._instance_state(actions[-1])
    later = engine.pipeline.stage_instances[1]
    later_before = fixtures.TestInstanceWorkflowEngine._instance_state(later)
    engine.reset_single_action_instance(actions[2])
    # A new engine represents the worker's later completion request.
    fresh = InstanceWorkflowEngine(engine.status_dal, engine.pipeline)
    fresh.complete_an_action(actions[2].id, outcome)
    assert fixtures.TestInstanceWorkflowEngine._instance_state(actions[-1]) == before
    assert fixtures.TestInstanceWorkflowEngine._instance_state(later) == later_before
    assert fresh.instances_to_add == []


def test_last_running_sibling_does_not_advance_isolated_workflow():
    engine, actions = build(['1:4', '1:1'])
    actions[3].status_id = S.INPROGRESS
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    engine.complete_an_action(actions[3].id, S.SUCCESS)
    assert engine.pipeline.stage_instances[1].status_id == S.SUCCESS
    assert engine.pipeline.status_id == S.SUCCESS


def test_pipeline_reset_clears_isolation_and_preserves_stage_order():
    engine, actions = build(['1:4,1', '1:1'])
    actions[2].isolated_retry = True
    engine.reset_pipeline()
    assert [a.status_id for a in actions] == [S.READY] * 4 + [S.NEW]
    assert all(a.isolated_retry is False for a in actions)
    assert engine.pipeline.stage_instances[1].workflow_instances[0].action_instances[0].status_id == S.NEW


def test_later_explicit_workflow_reset_is_not_blocked_by_completed_retry():
    engine, actions = build(['1:4', '1:1'])
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    later = engine.pipeline.stage_instances[1].workflow_instances[0].action_instances[0]
    engine.reset_action(later, complete_reset=False)
    assert later.workflow_instance.stage_instance.status_id == S.NEW
    assert all(not stage.suppress_downstream for stage in engine.pipeline.stage_instances)


def test_isolated_retry_finishes_without_waiting_for_excluded_new_steps():
    engine, actions = build(['1:4,1', '1:1'])
    actions[-1].status_id = S.NEW
    actions[-1].end_date = None
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    assert actions[-1].status_id == S.NEW
    assert engine.pipeline.status_id == S.CANCELED
    assert engine.pipeline.end_date is not None


def test_new_broad_reset_can_advance_after_an_isolated_sibling_workflow():
    engine, actions = build(['2:4-1', '1:1'])
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    sibling = engine.pipeline.stage_instances[0].workflow_instances[1].action_instances[0]
    engine.reset_action(sibling, complete_reset=False)
    engine.complete_an_action(sibling.id, S.SUCCESS)
    assert engine.pipeline.stage_instances[1].workflow_instances[0].action_instances[0].status_id == S.READY


def test_isolated_retry_does_not_report_success_with_unstarted_later_stage():
    engine, actions = build(['1:4', '1:1'])
    later = engine.pipeline.stage_instances[1]
    later.status_id = S.NEW
    later.end_date = None
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    assert later.status_id == S.NEW
    assert engine.pipeline.status_id == S.CANCELED


def test_isolated_retry_does_not_report_success_for_uninstantiated_stage():
    engine, actions = build(['1:4', '1:1'])
    engine.pipeline.stage_instances.pop()
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    assert engine.instances_to_add == []
    assert engine.pipeline.status_id == S.CANCELED


def test_legacy_true_can_advance_after_isolated_later_action():
    engine, actions = build(['1:1,1,1', '1:1'])
    for action in actions:
        action.action_id = action.order + 1
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    assert engine.reset_action(actions[1], complete_reset=True) == [actions[0].id, actions[1].id]
    assert actions[2].status_id == S.SUCCESS
    engine.complete_an_action(actions[0].id, S.SUCCESS)
    assert actions[1].status_id == S.READY


def test_isolated_completion_waits_for_recovering_sibling_workflow():
    engine, actions = build(['2:4-1', '1:1'])
    sibling = engine.pipeline.stage_instances[0].workflow_instances[1].action_instances[0]
    sibling.status_id = S.INPROGRESS
    engine.reset_single_action_instance(actions[2])
    engine.reset_action(sibling, complete_reset=False, preserve_stage_scope=True)
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    assert sibling.status_id == S.NEW
    assert sibling.workflow_instance.status_id == S.INPROGRESS
    assert engine.pipeline.status_id == S.INPROGRESS
    assert engine.pipeline.stage_instances[0].status_id == S.INPROGRESS
