import pytest
from rapid.lib.constants import StatusConstants as S
from rapid.workflow.data.models import ActionInstance, StageInstance
from rapid.workflow.workflow_engine import InstanceWorkflowEngine
from tests.master.util import test_instance_workflow_engine as fixtures


UNSTABLE = 9

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


def test_single_retry_uses_existing_database_schema():
    assert 'isolated_retry' not in ActionInstance.__table__.columns
    assert 'suppress_downstream' not in StageInstance.__table__.columns


@pytest.mark.parametrize('kind', ['Units', 'Static Analyzing'])
@pytest.mark.parametrize('outcome', [S.SUCCESS, S.FAILED, UNSTABLE, S.CANCELED])
def test_retry_third_slice_keeps_build_indexing_and_sibling_results(kind, outcome):
    engine, build_actions = build(['1:1', '2:4-1,4'])
    workflows = engine.pipeline.stage_instances[1].workflow_instances
    units, static = workflows
    selected_workflow = units if kind == 'Units' else static
    slices = selected_workflow.action_instances if kind == 'Units' else selected_workflow.action_instances[1:]
    target = slices[2]
    target.status_id = S.FAILED
    target.assigned_to = 'old-worker'
    others = [a for stage in engine.pipeline.stage_instances for w in stage.workflow_instances
              for a in w.action_instances if a.id != target.id]
    before = [fixtures.TestInstanceWorkflowEngine._instance_state(a) for a in others]
    assert engine.reset_single_action_instance(target) == [target.id]
    assert fixtures.TestInstanceWorkflowEngine._instance_state(target) == (S.READY, None, None, None)
    assert selected_workflow.status_id == S.INPROGRESS
    assert engine.pipeline.status_id == S.INPROGRESS
    assert engine.pipeline.end_date is None
    engine.complete_an_action(target.id, outcome)
    assert [fixtures.TestInstanceWorkflowEngine._instance_state(a) for a in others] == before
    assert build_actions[0].status_id == S.SUCCESS
    assert static.action_instances[0].status_id == S.SUCCESS
    assert target.status_id == outcome
    assert engine.pipeline.status_id == (S.SUCCESS if outcome == S.SUCCESS else S.CANCELED if outcome == S.CANCELED else S.FAILED)


@pytest.mark.parametrize('kind', ['Units', 'Static Analyzing'])
def test_slice_retry_waits_for_running_sibling(kind):
    engine, _ = build(['1:1', '2:4-1,4'])
    workflow = engine.pipeline.stage_instances[1].workflow_instances[0 if kind == 'Units' else 1]
    slices = workflow.action_instances if kind == 'Units' else workflow.action_instances[1:]
    target, sibling = slices[2], slices[3]
    sibling.status_id = S.INPROGRESS
    sibling.end_date = None
    engine.reset_single_action_instance(target)
    engine.complete_an_action(target.id, S.SUCCESS)
    assert sibling.status_id == S.INPROGRESS
    assert workflow.status_id == S.INPROGRESS
    assert engine.pipeline.status_id == S.INPROGRESS
    engine.complete_an_action(sibling.id, S.SUCCESS)
    assert engine.pipeline.status_id == S.SUCCESS


def test_single_retry_uses_normal_next_action_progression():
    engine, actions = build(['1:4,1'])
    actions[-1].status_id = S.NEW
    actions[-1].end_date = None
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    assert actions[-1].status_id == S.READY


def test_single_retry_uses_normal_next_stage_progression():
    engine, actions = build(['1:4', '1:1'])
    engine.reset_single_action_instance(actions[2])
    engine.complete_an_action(actions[2].id, S.SUCCESS)
    assert engine.pipeline.stage_instances[1].workflow_instances[0].action_instances[0].status_id == S.READY
