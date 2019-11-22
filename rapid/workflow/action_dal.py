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
# pylint: disable=singleton-comparison,broad-except
import logging
import datetime
import random

import time

from sqlalchemy import func, and_, asc
from sqlalchemy.orm import joinedload, aliased
from sqlalchemy.sql.expression import exists

from rapid.lib.exceptions import InvalidObjectException
from rapid.lib.store_service import StoreService
from rapid.lib.constants import StatusConstants, StatusTypes, ModuleConstants
from rapid.lib.work_request import WorkRequest
from rapid.lib.framework.injectable import Injectable
from rapid.lib.modules import QaModule
from rapid.lib import get_db_session
from rapid.workflow.workflow_engine import InstanceWorkflowEngine
from rapid.workflow.data.dal.status_dal import StatusDal
from rapid.workflow.data.models import ActionInstance, PipelineInstance, PipelineParameters, Status, \
    PipelineStatistics, Statistics, StageInstance, WorkflowInstance, ActionInstanceConfig
from rapid.master.data.database.dal.general_dal import GeneralDal
from rapid.workflow.event_service import EventService

logger = logging.getLogger('rapid')


class ActionDal(GeneralDal, Injectable):
    __injectables__ = {ModuleConstants.QA_MODULE: QaModule,
                       'store_service': StoreService,
                       'event_service': EventService,
                       'flask_app': None,
                       'status_dal': StatusDal,
                       'queue_constants': None}
    last_sent = None

    def __init__(self, qa_module=None, store_service=None, event_service=None, flask_app=None, status_dal=None, queue_constants=None):
        """

        :param qa_module: rapid.master.modules.modules.QaModule
        :type  store_service: StoreService
        :type event_service: EventService
        :type status_dal: StatusDal
        :return:
        """
        self.qa_module = qa_module
        self.store_service = store_service
        self.event_service = event_service
        self.flask_app = flask_app
        self.status_dal = status_dal
        self.queue_constants = queue_constants

    def _get_ready_work_requests(self, session, work_requests, results):
        """
        :param session:
        :type session: sqlalchemy.orm.scoping.scoped_session
        :param work_requests:
        :type work_requests: dict
        :param results:
        :type results: list
        :return:
        :rtype:
        """
        for action_instance, pipeline_parameters, action_instance_config in session.query(ActionInstance, PipelineParameters, ActionInstanceConfig) \
                .outerjoin(PipelineParameters, PipelineParameters.pipeline_instance_id == ActionInstance.pipeline_instance_id) \
                .outerjoin(ActionInstanceConfig, ActionInstanceConfig.action_instance_id == ActionInstance.id) \
                .filter(ActionInstance.status_id == StatusConstants.READY) \
                .filter(ActionInstance.manual == 0) \
                .filter(ActionInstance.pipeline_instance_id == PipelineInstance.id) \
                .filter(PipelineInstance.status_id == StatusConstants.INPROGRESS) \
                .order_by(PipelineInstance.priority.desc(),
                          PipelineInstance.created_date.asc(),
                          PipelineInstance.id.asc(),
                          ActionInstance.order.asc(),
                          ActionInstance.slice.asc()).all():
            self.configure_work_request(action_instance, pipeline_parameters, work_requests, results)

    def _get_stalled_work_requests(self, session, work_requests, results):
        """
        :param session:
        :type session:
        :param work_requests:
        :type work_requests: dict
        :param results:
        :type results: list
        :return:
        :rtype:
        """
        action_alias = aliased(ActionInstance)
        inner_query = ~exists()\
            .where(action_alias.workflow_instance_id == WorkflowInstance.id) \
            .where(action_alias.order < ActionInstance.order)\
            .where(action_alias.end_date == None)\
            .correlate(ActionInstance) \
            .correlate(WorkflowInstance)
        for action_instance, pipeline_parameters, action_instance_config in session.query(ActionInstance, PipelineParameters, ActionInstanceConfig) \
                .join(PipelineInstance, PipelineInstance.id == ActionInstance.pipeline_instance_id) \
                .join(WorkflowInstance, WorkflowInstance.id == ActionInstance.workflow_instance_id) \
                .outerjoin(PipelineParameters, PipelineParameters.pipeline_instance_id == ActionInstance.pipeline_instance_id) \
                .outerjoin(ActionInstanceConfig, ActionInstanceConfig.action_instance_id == ActionInstance.id) \
                .filter(ActionInstance.status_id == StatusConstants.NEW) \
                .filter(ActionInstance.manual == 0) \
                .filter(PipelineInstance.status_id == StatusConstants.INPROGRESS) \
                .filter(inner_query) \
                .order_by(PipelineInstance.priority.desc(),
                          PipelineInstance.created_date.asc(),
                          PipelineInstance.id.asc(),
                          ActionInstance.order.asc(),
                          ActionInstance.slice.asc()).all():
            action_instance.configuration = action_instance_config
            self.configure_work_request(action_instance, pipeline_parameters, work_requests, results)

    def configure_work_request(self, action_instance, pipeline_parameters, work_requests, results, include_configuration=True):
        """
        :param action_instance:
        :type action_instance: ActionInstance
        :param pipeline_parameters:
        :type pipeline_parameters: PipelineParameters
        :param results:
        :type results: list
        :return:
        :rtype:
        """
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

        if include_configuration:
            try:
                work_request.configuration = action_instance.configuration.configuration
            except (TypeError, AttributeError):
                pass

    def get_workable_work_requests(self):
        results = []
        for session in get_db_session():
            work_requests = {}
            self._get_ready_work_requests(session, work_requests, results)
            self._get_stalled_work_requests(session, work_requests, results)

        return results

    def get_verify_working(self, time_difference):
        results = []
        for session in get_db_session():
            for action_instance in session.query(ActionInstance).join(PipelineInstance) \
                    .filter(PipelineInstance.status_id == StatusConstants.INPROGRESS) \
                    .filter(ActionInstance.status_id == StatusConstants.INPROGRESS) \
                    .filter(ActionInstance.assigned_to != '') \
                    .filter(ActionInstance.start_date <= datetime.datetime.utcnow() - datetime.timedelta(minutes=time_difference)) \
                    .filter(ActionInstance.end_date.is_(None)) \
                    .filter(ActionInstance.manual == 0).all():
                results.append(action_instance.serialize())
        return results

    def get_work_request_by_action_instance_id(self, action_instance_id):
        for session in get_db_session():
            work_requests = {}
            results = []
            for action_instance, pipeline_parameters in session.query(ActionInstance, PipelineParameters) \
                    .outerjoin(PipelineParameters, PipelineParameters.pipeline_instance_id == ActionInstance.pipeline_instance_id)\
                    .filter(ActionInstance.id == action_instance_id).all():
                self.configure_work_request(action_instance, pipeline_parameters, work_requests, results, include_configuration=False)
            return results[0].__dict__
        return None

    def get_action_instance_by_id(self, _id, session=None):
        """
        Get ActionInstance by ID
        :param _id: long ID
        :param session: Possible db session to use
        :return: Action Instance
        :rtype ActionInstance
        """
        if session is None:
            for new_session in get_db_session():
                return new_session.query(ActionInstance).get(_id).serialize()
        return session.query(ActionInstance).get(_id)

    def complete_action_instance(self, _id, post_data):
        for session in get_db_session():
            action_instance = self.get_action_instance_by_id(_id, session)
            action_instance.end_date = datetime.datetime.utcnow()

            self.store_service.set_completing(_id)
            self._save_statistics(action_instance, session, post_data)
            self._save_status_information(action_instance, session, post_data)
            self.store_service.clear_completing(_id)

            session.commit()

        return True

    def callback_action_instance(self, _id, post_data):
        for session in get_db_session():
            self._save_status(self.get_action_instance_by_id(_id, session), session, post_data, True)
        return True

    def reset_pipeline_instance(self, pipeline_instance_id):
        for session in get_db_session():
            pipeline_instance = session.query(PipelineInstance)\
                                              .options(
                                                  joinedload(PipelineInstance.stage_instances)
                                                  .joinedload(StageInstance.workflow_instances)
                                                  .joinedload(WorkflowInstance.action_instances)).filter(PipelineInstance.id == pipeline_instance_id).first()

            instance_workflow_engine = InstanceWorkflowEngine(self.status_dal, pipeline_instance)
            instance_workflow_engine.reset_pipeline()
            session.commit()
        return True

    @staticmethod
    def _print_pipeline_instance(pipeline_instance):
        print("pipeline: {}, Status: {}, Start Date: {}, End Date:{}".format(pipeline_instance.id, pipeline_instance.status_id, pipeline_instance.start_date, pipeline_instance.end_date))
        for stage_instance in pipeline_instance.stage_instances:
            print("stage: {}, Status: {}, Start Date: {}, End Date: {}".format(stage_instance.id, stage_instance.status_id, stage_instance.start_date, stage_instance.end_date))
            for workflow_instance in stage_instance.workflow_instances:
                print("  workflow: {}, Status: {}, Start Date: {}, End Date: {}".format(workflow_instance.id, workflow_instance.status_id, workflow_instance.start_date, workflow_instance.end_date))
                for action_instance in workflow_instance.action_instances:
                    print("    action: {}, Status: {}, Start Date: {}, End Date: {}, Order: {}, Slice: {}".format(action_instance.id, action_instance.status_id, action_instance.start_date, action_instance.end_date, action_instance.order, action_instance.slice))

    def reset_action_instance(self, _id, complete_reset=False, check_status=False):  # pylint: disable=unused-argument
        for session in get_db_session():
            action_instance = session.query(ActionInstance).get(_id)
            if check_status and action_instance.status_id != StatusConstants.INPROGRESS:
                return False

            instance_workflow_engine = InstanceWorkflowEngine(self.status_dal, action_instance.pipeline_instance)
            instance_workflow_engine.reset_action(action_instance)

            if self.qa_module is not None:
                self.qa_module.reset_results(action_instance.id, session)
            
            session.commit()
        return True

    def cancel_action_instance(self, action_instance_id):
        for session in get_db_session():
            action_instance = self.get_action_instance_by_id(action_instance_id, session)

            if action_instance:
                serialized = action_instance.serialize()
                instance_workflow_engine = InstanceWorkflowEngine(StatusDal(session), action_instance.pipeline_instance)
                instance_workflow_engine.complete_an_action(action_instance_id, StatusConstants.CANCELED)
                self.queue_constants.cancel_worker(serialized)
                session.commit()
            else:
                raise InvalidObjectException("Action Instance not found", 404)
        return {"message": "Action Instance has been canceled."}

    def reconcile_pipeline_instances(self):
        for session in get_db_session():
            action_query = session.query(ActionInstance).filter(ActionInstance.status_id <= StatusConstants.INPROGRESS).subquery('ai')
            pipeline_instances = session.query(PipelineInstance).filter(PipelineInstance.status_id == StatusConstants.INPROGRESS)\
                .filter(~exists().where(PipelineInstance.id == action_query.c.pipeline_instance_id))
            
            for pipeline_instance in pipeline_instances.all():
                query = session.query(StageInstance, WorkflowInstance, ActionInstance).filter(and_(
                    StageInstance.pipeline_instance_id == pipeline_instance.id,
                    WorkflowInstance.stage_instance_id == StageInstance.id,
                    ActionInstance.workflow_instance_id == WorkflowInstance.id
                )).order_by(asc(StageInstance.id), asc(WorkflowInstance.id), asc(ActionInstance.id))

                highest_status_id = None
                highest_end_date = None
                mappings = {}
                for stage_instance, workflow_instance, action_instance in query.all():
                    if stage_instance.end_date is None:
                        work_name = 'workflow_{}'.format(workflow_instance.id)
                        if work_name not in mappings:
                            mappings[work_name] = {'obj': workflow_instance,
                                                   'highest_status_id': workflow_instance.status_id,
                                                   'highest_end_date': workflow_instance.end_date,
                                                   'stage_obj': stage_instance}

                        if workflow_instance.end_date is None:
                            workflow_check = mappings[work_name]
                            if workflow_check['highest_status_id'] < action_instance.status_id:
                                workflow_check['highest_status_id'] = action_instance.status_id

                            if (workflow_check['highest_end_date'] is None and action_instance.end_date) or \
                               (action_instance.end_date and workflow_check['highest_end_date'] < action_instance.end_date):
                                workflow_check['highest_end_date'] = action_instance.end_date

                for mapping in mappings.values():
                    workflow = mapping['obj']
                    stage = mapping['stage_obj']

                    workflow.status_id = mapping['highest_status_id']
                    workflow.end_date = mapping['highest_end_date']
                    
                    if stage.status_id < workflow.status_id:
                        stage.status_id = workflow.status_id
                        highest_status_id = stage.status_id

                    if (stage.end_date is None and workflow.end_date) or (workflow.end_date and stage.end_date < workflow.end_date):
                        stage.end_date = workflow.end_date
                        highest_end_date = stage.end_date

                if highest_status_id is not None and highest_end_date is not None:
                    logger.info("Reconciling PipelineInstance: {}".format(pipeline_instance.id))
                    pipeline_instance.status_id = highest_status_id
                    pipeline_instance.end_date = highest_end_date

            session.commit()

    def _wait_for_parallel_calculations(self, action_instance):
        is_calculating = StoreService.is_calculating_workflow(action_instance.pipeline_instance_id)
        if is_calculating:
            count = 0
            while count < 5 and is_calculating:
                time.sleep(.1)
                is_calculating = StoreService.is_calculating_workflow(action_instance.pipeline_instance_id)
                count += 1

    def _save_status(self, action_instance, session, post_data, allow_save=False):
        if 'status' in post_data:
            status = self.get_status_by_name(post_data['status'], session)

            if action_instance.callback_required and status.type == StatusTypes.SUCCESS and not allow_save:
                # Allow_save comes from callback_method.
                return

            self._wait_for_parallel_calculations(action_instance)

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

    def _save_statistics(self, action_instance, session, post_data):
        try:
            self._save_parameters(action_instance.pipeline_instance_id, session, post_data)
            self._save_stats(action_instance.pipeline_instance_id, session, post_data)
            if self.qa_module is not None:
                self.qa_module.save_results(action_instance, session, post_data)
        except Exception as exception:
            logger.error(exception)

    def _save_status_information(self, action_instance, session, post_data):
        check = '{}__{}'.format(action_instance.pipeline_instance_id, action_instance.action_id)
        if self.store_service.is_completing(check):
            time.sleep(random.randint(3, 10) * 0.01)

        self.store_service.set_completing(check)
        try:
            self._save_status(action_instance, session, post_data)
        except Exception as exception:
            logger.error(exception)
        self.store_service.clear_completing(check)

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

    def _save_stats(self, pipeline_instance_id, session, post_data):  # pylint: disable=too-many-locals
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
                except Exception:
                    import traceback
                    traceback.print_exc()

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

    def partial_edit(self, _id, changes):
        for session in get_db_session():
            return self.edit_object(session, ActionInstance, _id, changes).serialize()

    def get_status_by_name(self, name, session=None):
        if session is not None:
            return session.query(Status).filter(func.lower(Status.name) == name.lower()).first()

        for new_session in get_db_session():
            status = new_session.query(Status).filter(func.lower(Status.name) == name.lower()).first()
            return status.serialize() if status else None
