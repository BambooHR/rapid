import datetime
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from rapid.lib.constants import StatusConstants, StatusTypes
from rapid.workflow.action_dal import ActionDal
from rapid.workflow.data.models import (
    Action,
    ActionInstance,
    Pipeline,
    PipelineInstance,
    PipelineParameters,
    Stage,
    StageInstance,
    Status,
    Workflow,
    WorkflowInstance,
)


def _create_db():
    database = create_engine('sqlite://')
    for model in (
        Status,
        Pipeline,
        Stage,
        Workflow,
        Action,
        PipelineInstance,
        PipelineParameters,
        StageInstance,
        WorkflowInstance,
        ActionInstance,
    ):
        model.__table__.create(database)
    with Session(database) as session:
        session.add_all([
            Status(id=StatusConstants.NEW, name='NEW', display_name='New', type=StatusTypes.SUCCESS),
            Status(id=StatusConstants.READY, name='READY', display_name='Ready', type=StatusTypes.SUCCESS),
            Status(id=StatusConstants.INPROGRESS, name='INPROGRESS', display_name='In Progress', type=StatusTypes.SUCCESS),
            Status(id=StatusConstants.SUCCESS, name='SUCCESS', display_name='Success', type=StatusTypes.SUCCESS),
            Status(id=StatusConstants.FAILED, name='FAILED', display_name='Failed', type=StatusTypes.FAILED),
            Status(id=StatusConstants.CANCELED, name='CANCELED', display_name='Canceled', type=StatusTypes.CANCELED),
        ])
        session.commit()
    return database


def _seed_two_workflow_pipeline(database, coverage_status, sibling_status, stage_status, pipeline_status):
    now = datetime.datetime.utcnow()
    with Session(database) as session:
        pipeline_def = Pipeline(id=1, name='pr-pipeline')
        stage_def = Stage(id=1, name='verify', pipeline_id=1, order=0)
        coverage_wf_def = Workflow(id=1, name='coverage', stage_id=1, order=0)
        sibling_wf_def = Workflow(id=2, name='integrations', stage_id=1, order=0)

        pipeline = PipelineInstance(
            id=10,
            pipeline_id=1,
            status_id=pipeline_status,
            created_date=now,
            start_date=now,
            end_date=now if pipeline_status in (StatusConstants.SUCCESS, StatusConstants.FAILED) else None,
        )
        stage = StageInstance(
            id=100,
            stage_id=1,
            order=0,
            pipeline_instance=pipeline,
            status_id=stage_status,
            start_date=now,
            end_date=now if stage_status in (StatusConstants.SUCCESS, StatusConstants.FAILED) else None,
        )
        coverage_wf = WorkflowInstance(
            id=1000,
            workflow_id=1,
            order=0,
            stage_instance=stage,
            status_id=coverage_status,
            start_date=now,
            end_date=now if coverage_status == StatusConstants.FAILED else None,
        )
        sibling_wf = WorkflowInstance(
            id=1001,
            workflow_id=2,
            order=0,
            stage_instance=stage,
            status_id=sibling_status,
            start_date=now,
            end_date=now if sibling_status in (StatusConstants.SUCCESS, StatusConstants.FAILED) else None,
        )
        coverage_action = ActionInstance(
            id=5000,
            action_id=1,
            order=0,
            cmd='coverage',
            executable='coverage',
            args='',
            pipeline_instance=pipeline,
            workflow_instance=coverage_wf,
            status_id=coverage_status,
            start_date=now,
            end_date=now if coverage_status == StatusConstants.FAILED else None,
        )
        sibling_action = ActionInstance(
            id=5001,
            action_id=2,
            order=0,
            cmd='integrations',
            executable='integrations',
            args='',
            pipeline_instance=pipeline,
            workflow_instance=sibling_wf,
            status_id=sibling_status,
            start_date=now,
            end_date=now if sibling_status in (StatusConstants.SUCCESS, StatusConstants.FAILED) else None,
        )
        session.add_all([
            pipeline_def,
            stage_def,
            coverage_wf_def,
            sibling_wf_def,
            pipeline,
            stage,
            coverage_wf,
            sibling_wf,
            coverage_action,
            sibling_action,
        ])
        session.commit()


def test_callback_override_while_sibling_runs_lets_pipeline_succeed():
    database = _create_db()
    _seed_two_workflow_pipeline(
        database,
        coverage_status=StatusConstants.FAILED,
        sibling_status=StatusConstants.INPROGRESS,
        stage_status=StatusConstants.INPROGRESS,
        pipeline_status=StatusConstants.INPROGRESS,
    )

    with Session(database) as session:
        dal = ActionDal(event_service=Mock())
        with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
            assert dal.callback_action_instance(5000, {'status': 'SUCCESS'}) is True

    with Session(database) as session:
        assert session.get(ActionInstance, 5000).status_id == StatusConstants.SUCCESS
        assert session.get(WorkflowInstance, 1000).status_id == StatusConstants.SUCCESS
        assert session.get(StageInstance, 100).status_id == StatusConstants.INPROGRESS
        assert session.get(PipelineInstance, 10).status_id == StatusConstants.INPROGRESS

    with Session(database) as session:
        dal = ActionDal(event_service=Mock())
        with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
            assert dal.callback_action_instance(5001, {'status': 'SUCCESS'}) is True

    with Session(database) as session:
        assert session.get(WorkflowInstance, 1001).status_id == StatusConstants.SUCCESS
        assert session.get(StageInstance, 100).status_id == StatusConstants.SUCCESS
        pipeline = session.get(PipelineInstance, 10)
        assert pipeline.status_id == StatusConstants.SUCCESS
        assert pipeline.end_date is not None


def test_callback_override_preserves_sibling_failure():
    database = _create_db()
    _seed_two_workflow_pipeline(
        database,
        coverage_status=StatusConstants.FAILED,
        sibling_status=StatusConstants.FAILED,
        stage_status=StatusConstants.FAILED,
        pipeline_status=StatusConstants.FAILED,
    )

    with Session(database) as session:
        dal = ActionDal(event_service=Mock())
        with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
            assert dal.callback_action_instance(5000, {'status': 'SUCCESS'}) is True

    with Session(database) as session:
        assert session.get(ActionInstance, 5000).status_id == StatusConstants.SUCCESS
        assert session.get(WorkflowInstance, 1000).status_id == StatusConstants.SUCCESS
        assert session.get(WorkflowInstance, 1001).status_id == StatusConstants.FAILED
        assert session.get(StageInstance, 100).status_id == StatusConstants.FAILED
        assert session.get(PipelineInstance, 10).status_id == StatusConstants.FAILED


def test_callback_override_after_sibling_succeeded_rolls_up_pipeline_to_success():
    database = _create_db()
    _seed_two_workflow_pipeline(
        database,
        coverage_status=StatusConstants.FAILED,
        sibling_status=StatusConstants.SUCCESS,
        stage_status=StatusConstants.FAILED,
        pipeline_status=StatusConstants.FAILED,
    )

    with Session(database) as session:
        dal = ActionDal(event_service=Mock())
        with patch('rapid.workflow.action_dal.get_db_session', return_value=[session]):
            assert dal.callback_action_instance(5000, {'status': 'SUCCESS'}) is True

    with Session(database) as session:
        assert session.get(ActionInstance, 5000).status_id == StatusConstants.SUCCESS
        assert session.get(WorkflowInstance, 1000).status_id == StatusConstants.SUCCESS
        assert session.get(StageInstance, 100).status_id == StatusConstants.SUCCESS
        assert session.get(PipelineInstance, 10).status_id == StatusConstants.SUCCESS
