import pytest
from rapid.lib.constants import StatusConstants
from rapid.workflow.workflow_engine import InstanceWorkflowEngine
from tests.master.util import test_instance_workflow_engine as fixtures


def build(layout):
    fixture = fixtures.TestInstanceWorkflowEngine()
    pipeline = fixture._build_pipeline_instance(layout, completed=True)
    pipeline.id = 4311
    for i, stage in enumerate(pipeline.stage_instances):
        stage.order = i
        stage.stage_id = stage.id
        for workflow in stage.workflow_instances:
            for action in workflow.action_instances:
                action.action_id = workflow.id * 100 + action.order
    engine = InstanceWorkflowEngine(fixture._get_mocked_dal(), pipeline)
    return engine, pipeline.stage_instances[0].workflow_instances[0].action_instances


@pytest.mark.parametrize('kind', ['Units', 'Static Analyzing'])
@pytest.mark.parametrize('outcome', [StatusConstants.SUCCESS, StatusConstants.FAILED])
def test_retry_third_slice_keeps_build_indexing_and_sibling_results(kind, outcome):
    engine, build_actions = build(['1:1', '2:4-1,4'])
    workflows = engine.pipeline.stage_instances[1].workflow_instances
    units, static = workflows
    selected_workflow = units if kind == 'Units' else static
    slices = selected_workflow.action_instances if kind == 'Units' else selected_workflow.action_instances[1:]
    target = slices[2]
    target.status_id = StatusConstants.FAILED
    target.assigned_to = 'old-worker'
    others = [action for stage in engine.pipeline.stage_instances for workflow in stage.workflow_instances
              for action in workflow.action_instances if action.id != target.id]
    before = [fixtures.TestInstanceWorkflowEngine._instance_state(action) for action in others]
    assert engine.reset_single_action_instance(target) == [target.id]
    assert fixtures.TestInstanceWorkflowEngine._instance_state(target) == (StatusConstants.READY, None, None, None)
    assert selected_workflow.status_id == StatusConstants.INPROGRESS
    assert engine.pipeline.status_id == StatusConstants.INPROGRESS
    assert engine.pipeline.end_date is None
    engine.complete_an_action(target.id, outcome)
    assert [fixtures.TestInstanceWorkflowEngine._instance_state(action) for action in others] == before
    assert build_actions[0].status_id == StatusConstants.SUCCESS
    assert static.action_instances[0].status_id == StatusConstants.SUCCESS
    assert target.status_id == outcome
    assert engine.pipeline.status_id == outcome


def test_slice_retry_waits_for_running_sibling():
    engine, _ = build(['1:1', '2:4-1,4'])
    workflow = engine.pipeline.stage_instances[1].workflow_instances[0]
    target, sibling = workflow.action_instances[2], workflow.action_instances[3]
    sibling.status_id = StatusConstants.INPROGRESS
    sibling.end_date = None
    engine.reset_single_action_instance(target)
    engine.complete_an_action(target.id, StatusConstants.SUCCESS)
    assert sibling.status_id == StatusConstants.INPROGRESS
    assert workflow.status_id == StatusConstants.INPROGRESS
    assert engine.pipeline.status_id == StatusConstants.INPROGRESS
    engine.complete_an_action(sibling.id, StatusConstants.SUCCESS)
    assert engine.pipeline.status_id == StatusConstants.SUCCESS


def test_single_retry_uses_normal_next_stage_progression():
    engine, actions = build(['1:4', '1:1'])
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, StatusConstants.SUCCESS)
    assert engine.pipeline.stage_instances[1].workflow_instances[0].action_instances[0].status_id == StatusConstants.READY
