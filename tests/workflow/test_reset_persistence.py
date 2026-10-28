import datetime
from unittest.mock import Mock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from rapid.lib.constants import StatusConstants as S
from rapid.workflow.action_dal import ActionDal
from rapid.workflow.data.models import ActionInstance, ActionInstanceConfig, PipelineInstance, PipelineParameters, StageInstance, WorkflowInstance


@pytest.mark.parametrize('kind', ['Units', 'Static Analyzing'])
def test_retry_persists_and_dispatches_only_selected_slice_on_existing_schema(kind):
    database = create_engine('sqlite://')
    for model in (PipelineInstance, PipelineParameters, StageInstance, WorkflowInstance, ActionInstance, ActionInstanceConfig):
        model.__table__.create(database)
    now = datetime.datetime.utcnow()
    with Session(database) as session:
        pipeline = PipelineInstance(id=1, pipeline_id=1, status_id=S.FAILED, created_date=now, end_date=now)
        stage = StageInstance(id=1, stage_id=1, order=0, pipeline_instance=pipeline, status_id=S.FAILED, end_date=now)
        workflow = WorkflowInstance(id=1, workflow_id=1, stage_instance=stage, status_id=S.FAILED, end_date=now)
        common = dict(cmd='test', executable='test', args='', pipeline_instance=pipeline, workflow_instance=workflow,
                      start_date=now, end_date=now, assigned_to='old-worker')
        actions = []
        if kind == 'Static Analyzing':
            actions.append(ActionInstance(id=1, action_id=10, order=0, status_id=S.SUCCESS, **common))
        for index in range(4):
            actions.append(ActionInstance(id=10 + index, action_id=20, order=1 if kind == 'Static Analyzing' else 0,
                                          slice=f'{index + 1}/4', status_id=S.FAILED if index == 2 else S.SUCCESS, **common))
        session.add_all([pipeline, stage, workflow] + actions)
        session.commit()
        qa = Mock()
        with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
            result = ActionDal(qa_module=qa, status_dal=Mock()).reset_action_instance(12, reset_single_slice=True)
        assert result == {'action_instance_id': 12, 'outcome': 'reset'}
        qa.reset_results.assert_called_once_with(12, session, commit=False)
    with Session(database) as session:
        selected = session.get(ActionInstance, 12)
        assert selected.status_id == S.READY
        assert selected.start_date is None and selected.end_date is None and selected.assigned_to is None
        assert selected.pipeline_instance.status_id == S.INPROGRESS
        for other in session.query(ActionInstance).filter(ActionInstance.id != 12):
            assert (other.status_id, other.start_date, other.end_date, other.assigned_to) == (S.SUCCESS, now, now, 'old-worker')
        dal = ActionDal()
        requests = []
        dal._get_ready_work_requests(session, {}, requests)
        assert [request.action_instance_id for request in requests] == [12]
        requests = []
        dal._get_stalled_work_requests(session, {}, requests)
        assert requests == []
