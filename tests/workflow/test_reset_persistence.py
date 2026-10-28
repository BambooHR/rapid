import datetime
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from rapid.lib.constants import StatusConstants as S
from rapid.workflow.action_dal import ActionDal
from rapid.workflow.data.models import ActionInstance, ActionInstanceConfig, PipelineInstance, PipelineParameters, StageInstance, WorkflowInstance
from rapid.workflow.workflow_engine import InstanceWorkflowEngine


def test_persisted_retry_blocks_stalled_steps_but_allows_later_explicit_reset():
    database = create_engine('sqlite://')
    for model in (PipelineInstance, PipelineParameters, StageInstance, WorkflowInstance, ActionInstance, ActionInstanceConfig):
        model.__table__.create(database)
    with Session(database) as session:
        pipeline = PipelineInstance(id=1, pipeline_id=1, status_id=S.INPROGRESS)
        first = StageInstance(id=1, stage_id=1, order=0, pipeline_instance=pipeline, status_id=S.INPROGRESS, suppress_downstream=True)
        later = StageInstance(id=2, stage_id=2, order=1, pipeline_instance=pipeline, status_id=S.NEW)
        workflow = WorkflowInstance(id=1, workflow_id=1, stage_instance=first, status_id=S.INPROGRESS)
        following = WorkflowInstance(id=2, workflow_id=2, stage_instance=later, status_id=S.NEW)
        common = dict(cmd='test', executable='test', args='', pipeline_instance=pipeline)
        retry = ActionInstance(id=1, action_id=1, workflow_instance=workflow, order=0, status_id=S.SUCCESS,
                               isolated_retry=True, end_date=datetime.datetime.utcnow(), **common)
        waiting = ActionInstance(id=2, action_id=2, workflow_instance=workflow, order=1, status_id=S.NEW, **common)
        next_stage = ActionInstance(id=3, action_id=3, workflow_instance=following, order=0, status_id=S.NEW, **common)
        session.add_all([pipeline, first, later, workflow, following, retry, waiting, next_stage])
        session.commit()
    with Session(database) as session:
        retry = session.get(ActionInstance, 1)
        assert retry.isolated_retry is True
        assert retry.workflow_instance.stage_instance.suppress_downstream is True
        dal = ActionDal()
        results = []
        dal._get_stalled_work_requests(session, {}, results)
        assert results == []
        # Retry is explicitly queued; persisted isolation must not block that ID.
        retry.status_id = S.READY
        session.flush()
        dal._get_ready_work_requests(session, {}, results)
        assert [request.action_instance_id for request in results] == [1]
        retry.status_id = S.SUCCESS
        selected = session.get(ActionInstance, 3)
        InstanceWorkflowEngine(Mock(), selected.pipeline_instance).reset_action(selected, complete_reset=False)
        session.flush()
        results = []
        dal._get_stalled_work_requests(session, {}, results)
        assert [request.action_instance_id for request in results] == [3]


def test_retry_migration_preserves_existing_rows_and_can_be_reversed():
    import importlib
    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from unittest.mock import patch

    migration = importlib.import_module('rapid.master.data.migrations.versions.4311a27b1027_isolated_retry')
    database = create_engine('sqlite://')
    with database.begin() as connection:
        for table in ('action_instances', 'stage_instances'):
            connection.execute(sa.text('CREATE TABLE ' + table + ' (id INTEGER PRIMARY KEY)'))
            connection.execute(sa.text('INSERT INTO ' + table + ' (id) VALUES (1)'))
        with patch.object(migration, 'op', Operations(MigrationContext.configure(connection))):
            migration.upgrade()
            assert connection.execute(sa.text('SELECT isolated_retry FROM action_instances')).scalar() == 0
            assert connection.execute(sa.text('SELECT suppress_downstream FROM stage_instances')).scalar() == 0
            migration.downgrade()
        assert [column['name'] for column in sa.inspect(connection).get_columns('action_instances')] == ['id']
        assert [column['name'] for column in sa.inspect(connection).get_columns('stage_instances')] == ['id']


def test_normal_worker_recovery_remains_dispatchable_during_isolated_retry():
    database = create_engine('sqlite://')
    for model in (PipelineInstance, PipelineParameters, StageInstance, WorkflowInstance, ActionInstance, ActionInstanceConfig):
        model.__table__.create(database)
    with Session(database) as session:
        pipeline = PipelineInstance(id=1, pipeline_id=1, status_id=S.INPROGRESS)
        stage = StageInstance(id=1, stage_id=1, order=0, pipeline_instance=pipeline,
                              status_id=S.INPROGRESS, suppress_downstream=True)
        isolated = WorkflowInstance(id=1, workflow_id=1, stage_instance=stage, status_id=S.INPROGRESS)
        normal = WorkflowInstance(id=2, workflow_id=2, stage_instance=stage, status_id=S.INPROGRESS)
        common = dict(cmd='test', executable='test', args='', pipeline_instance=pipeline)
        retry = ActionInstance(id=1, action_id=1, workflow_instance=isolated, order=0,
                               status_id=S.INPROGRESS, isolated_retry=True, **common)
        recovery = ActionInstance(id=2, action_id=2, workflow_instance=normal, order=0,
                                  status_id=S.INPROGRESS, **common)
        session.add_all([pipeline, stage, isolated, normal, retry, recovery])
        session.commit()
        InstanceWorkflowEngine(Mock(), pipeline).reset_action(recovery, complete_reset=False, preserve_stage_scope=True)
        session.flush()
        results = []
        ActionDal()._get_stalled_work_requests(session, {}, results)
        assert [request.action_instance_id for request in results] == [2]
        assert stage.suppress_downstream is True
        assert retry.status_id == S.INPROGRESS


def test_unisolated_pipeline_keeps_legacy_new_stage_dispatch():
    database = create_engine('sqlite://')
    for model in (PipelineInstance, PipelineParameters, StageInstance, WorkflowInstance, ActionInstance, ActionInstanceConfig):
        model.__table__.create(database)
    with Session(database) as session:
        pipeline = PipelineInstance(id=1, pipeline_id=1, status_id=S.INPROGRESS)
        stage = StageInstance(id=1, stage_id=1, order=0, pipeline_instance=pipeline, status_id=S.NEW)
        workflow = WorkflowInstance(id=1, workflow_id=1, stage_instance=stage, status_id=S.NEW)
        action = ActionInstance(id=1, action_id=1, workflow_instance=workflow, order=0, status_id=S.NEW,
                                cmd='test', executable='test', args='', pipeline_instance=pipeline)
        session.add_all([pipeline, stage, workflow, action])
        session.commit()
        results = []
        ActionDal()._get_stalled_work_requests(session, {}, results)
        assert [request.action_instance_id for request in results] == [1]
