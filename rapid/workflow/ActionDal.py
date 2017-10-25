"""
 Copyright (c) 2015 Michael Bright and Bamboo HR LLC

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
"""

import datetime

from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import asc

from rapid.lib.StoreService import StoreService
from rapid.lib.Constants import StatusConstants, StatusTypes, ModuleConstants
from rapid.lib.WorkRequest import WorkRequest
from rapid.lib.framework.Injectable import Injectable
from rapid.lib.modules.modules import QaModule
from rapid.master.data.database import get_db_session
from rapid.workflow.WorkflowEngine import InstanceWorkflowEngine
from rapid.workflow.data.dal.StatusDal import StatusDal
from rapid.workflow.data.models import ActionInstance, PipelineInstance, PipelineParameters, Status, \
    PipelineStatistics, Statistics, StageInstance, WorkflowInstance

from rapid.master.data.database.dal.GeneralDal import GeneralDal
from rapid.workflow.EventService import EventService


class ActionDal(GeneralDal, Injectable):
    __injectables__ = {ModuleConstants.QA_MODULE: QaModule, 'store_service': StoreService, 'event_service': EventService}
    last_sent = None

    def __init__(self, qa_module=None, store_service=None, event_service=None):
        """

        :param qa_module: rapid.master.modules.modules.QaModule
        :type  store_service: StoreService
        :type event_service: EventService
        :return:
        """
        self.qa_module = qa_module
        self.store_service = store_service
        self.event_service = event_service

    def get_workable_work_requests(self):
        results = []
        for session in get_db_session():
            work_requests = {}
            for action_instance, pipeline_parameters in session.query(ActionInstance, PipelineParameters) \
                    .outerjoin(PipelineParameters, PipelineParameters.pipeline_instance_id == ActionInstance.pipeline_instance_id) \
                    .filter(ActionInstance.status_id == StatusConstants.READY) \
                    .filter(ActionInstance.manual == 0) \
                    .filter(ActionInstance.pipeline_instance_id == PipelineInstance.id) \
                    .filter(PipelineInstance.status_id == StatusConstants.INPROGRESS) \
                    .order_by(PipelineInstance.priority.desc(),
                              PipelineInstance.created_date.asc(),
                              PipelineInstance.id.asc(),
                              ActionInstance.order.asc(),
                              ActionInstance.slice.asc()).all():
                work_request = None
                if action_instance.id not in work_requests:
                    work_request = WorkRequest(action_instance.serialize())
                    work_request.action_instance_id = action_instance.id
                    work_request.pipeline_instance_id = action_instance.pipeline_instance_id
                    work_request.workflow_instance_id = action_instance.workflow_instance_id
                    work_request.slice = action_instance.slice
                    results.append(work_request)
                    work_requests[action_instance.id] = work_request
                else:
                    work_request = work_requests[action_instance.id]

                if pipeline_parameters:
                    work_request.environment[pipeline_parameters.parameter] = pipeline_parameters.value
        return results

    def get_verify_working(self, time_difference):
        results = []
        for session in get_db_session():
            for action_instance in session.query(ActionInstance).join(PipelineInstance) \
                    .filter(PipelineInstance.status_id == StatusConstants.INPROGRESS) \
                    .filter(ActionInstance.status_id == StatusConstants.INPROGRESS) \
                    .filter(ActionInstance.start_date <= datetime.datetime.utcnow() - datetime.timedelta(minutes=time_difference)) \
                    .filter(ActionInstance.end_date.is_(None)) \
                    .filter(ActionInstance.manual == 0).all():
                results.append(action_instance.serialize())
        return results

    def get_action_instance_by_id(self, id, session=None):
        """
        Get ActionInstance by ID
        :param id: long ID
        :param session: Possible db session to use
        :return: Action Instance
        :rtype ActionInstance
        """
        if session is None:
            for session in get_db_session():
                return session.query(ActionInstance).get(id).serialize()
        else:
            return session.query(ActionInstance).get(id)

    def complete_action_instance(self, id, post_data):
        for session in get_db_session():
            action_instance = self.get_action_instance_by_id(id, session)
            action_instance.end_date = datetime.datetime.utcnow()

            self.store_service.set_completing(id)
            try:
                self._save_parameters(action_instance.pipeline_instance_id, session, post_data)
                self._save_status(action_instance, session, post_data)
                self._save_stats(action_instance.pipeline_instance_id, session, post_data)
                if self.qa_module is not None:
                    self.qa_module.save_results(action_instance, session, post_data)
            except:
                import traceback
                traceback.print_exc()
            finally:
                self.store_service.clear_completing(id)

            session.commit()

        return True

    def callback_action_instance(self, id, post_data):
        for session in get_db_session():
            self._save_status(self.get_action_instance_by_id(id, session), session, post_data, True)
        return True

    def reset_pipeline_instance(self, pipeline_instance_id):
        for session in get_db_session():
            now = datetime.datetime.utcnow()
            pipeline_instance = session.query(PipelineInstance).get(pipeline_instance_id)
            pipeline_instance.status_id = StatusConstants.INPROGRESS
            pipeline_instance.start_date = now
            pipeline_instance.end_date = None

            first_stage = True
            for stage_instance in session.query(StageInstance).filter(StageInstance.pipeline_instance_id == pipeline_instance_id).all():
                stage_instance.status_id = StatusConstants.READY
                stage_instance.created_date = now
                stage_instance.start_date = now if first_stage else None
                stage_instance.end_date = None
                for workflow_instance in stage_instance.workflow_instances:
                    workflow_instance.status_id = StatusConstants.READY
                    workflow_instance.start_date = now if first_stage else None
                    workflow_instance.end_date = None
                first_stage = False

            return self.reset_action_instance(session.query(ActionInstance)\
                                       .filter(ActionInstance.pipeline_instance_id == pipeline_instance_id)\
                                       .order_by(asc(ActionInstance.order)).first().id, True)

    def reset_action_instance(self, id, complete_reset=False, check_status=False):
        for session in get_db_session():
            now = datetime.datetime.utcnow()
            action_instance = session.query(ActionInstance).get(id)
            if check_status and action_instance.status_id != StatusConstants.INPROGRESS:
                return False

            action_instance.assigned_to = None
            action_instance.status_id = StatusConstants.NEW if complete_reset else StatusConstants.READY
            action_instance.created_date = now
            action_instance.start_date = None
            action_instance.end_date = None

            action_instance.pipeline_instance.status_id = StatusConstants.INPROGRESS

            if self.qa_module is not None:
                self.qa_module.reset_results(action_instance.id, session)

            if complete_reset:
                current_order = action_instance.order
                first = True
                for instance in action_instance.workflow_instance.action_instances:
                    if instance.order < current_order or instance.id == id or instance.order == current_order:
                        instance.status_id = StatusConstants.NEW if not first else StatusConstants.READY
                        instance.start_date = None
                        instance.assigned_to = None
                        instance.end_date = None

                        if first:
                            first = False
                    elif instance.order == current_order:
                        continue
                    else:
                        break

                action_instance.workflow_instance.status_id = StatusConstants.INPROGRESS
                action_instance.workflow_instance.stage_instance.status_id = StatusConstants.INPROGRESS
                action_instance.pipeline_instance.status_id = StatusConstants.INPROGRESS
            session.commit()
        return True

    def _save_status(self, action_instance, session, post_data, allow_save=False):
        if 'status' in post_data:
            status = self.get_status_by_name(post_data['status'], session)

            if action_instance.callback_required and status.type == StatusTypes.SUCCESS and not allow_save:
                # Allow_save comes from callback_method.
                return
            pipeline_instance = session.query(PipelineInstance).options(
                    joinedload(PipelineInstance.stage_instances)
                        .joinedload(StageInstance.workflow_instances)
                        .joinedload(WorkflowInstance.action_instances)
            ).options(joinedload(PipelineInstance.parameters)).get(action_instance.pipeline_instance_id)
            workflow_engine = InstanceWorkflowEngine(StatusDal(session), pipeline_instance)
            workflow_engine.complete_an_action(action_instance.id, status.id)
            for instance in workflow_engine.instances_to_add:
                session.add(instance)
            session.commit()

            self.event_service.trigger_possible_event(pipeline_instance, action_instance, session)

    def _save_parameters(self, pipeline_instance_id, session, post_data):
        if 'parameters' in post_data:
            parameters_hash = {}
            for pipeline_parameter in session.query(PipelineParameters).filter(PipelineParameters.pipeline_instance_id == pipeline_instance_id).all():
                parameters_hash[pipeline_parameter.parameter] = pipeline_parameter

            for key, value in post_data['parameters'].items():
                pipeline_parameter = None
                if key in parameters_hash:
                    pipeline_parameter = parameters_hash[key]
                else:
                    pipeline_parameter = PipelineParameters(pipeline_instance_id=pipeline_instance_id)
                    session.add(pipeline_parameter)
                pipeline_parameter.parameter = str(key)
                pipeline_parameter.value = str(value)
            session.commit()

    def _save_stats(self, pipeline_instance_id, session, post_data):
        if 'stats' in post_data:
            statistics_cache = {}
            stats_needed = post_data['stats'].keys()

            for stat in session.query(Statistics).filter(Statistics.name.in_(post_data['stats'].keys())):
                try:
                    if stat.name in stats_needed:
                        clone_stats = list(stats_needed)
                        for index, item in enumerate(stats_needed):
                            if item == stat.name:
                                del clone_stats[index]
                                break
                        stats_needed = clone_stats
                    statistics_cache[stat.name] = stat
                except:
                    import traceback
                    traceback.print_exc()
                    pass

            for stat_to_create in stats_needed:
                stat = Statistics(name=stat_to_create)
                session.add(stat)

                statistics_cache[stat.name] = stat

            session.flush()
            session.commit()

            for key, value in post_data['stats'].items():
                stats = PipelineStatistics(pipeline_instance_id=pipeline_instance_id, statistics_id=statistics_cache[key].id, value=value)
                session.add(stats)

            session.commit()

    def partial_edit(self, id, changes):
        for session in get_db_session():
            return self.edit_object(session, ActionInstance, id, changes).serialize()

    def get_status_by_name(self, name, session=None):
        if session is not None:
            return session.query(Status).filter(func.lower(Status.name) == name.lower()).first()
        else:
            for session in get_db_session():
                status = session.query(Status).filter(func.lower(Status.name) == name.lower()).first()
                return status.serialize() if status else None
