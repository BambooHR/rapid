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
# pylint: disable=broad-except
import logging
import datetime

try:
    import simplejson as out_json
except ImportError:
    import json as out_json


from flask import request
from flask.wrappers import Response
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.sql.expression import asc

from rapid.lib.exceptions import InvalidObjectException
from rapid.lib.store_service import StoreService
from rapid.workflow.data.models import PipelineEvent
from rapid.lib import api_key_required, get_db_session
from rapid.lib.constants import StatusConstants, ModuleConstants
from rapid.lib.exceptions import VcsNotFoundException
from rapid.lib.framework.injectable import Injectable
from rapid.lib.modules import CiModule
from rapid.master.data.database.dal.general_dal import GeneralDal
from rapid.workflow.data.models import Action, Pipeline, Stage, Workflow, PipelineInstance, PipelineParameters


logger = logging.getLogger("rapid")


class PipelineDal(GeneralDal, Injectable):
    __injectables__ = {ModuleConstants.CI_MODULE: CiModule, 'flask_app': None, 'queue_constants': None}

    def __init__(self, ci_module, queue_constants, flask_app=None):
        """

        :type ci_module: :class:`rapid.lib.modules.modules.CiModule`
        :type queue_constants: QueueHandlerConstants
        :param flask_app: Flask
        :return:
        """
        super(PipelineDal, self).__init__()
        self.app = flask_app
        self.ci_module = ci_module
        self.queue_constants = queue_constants

    def is_serviceable(self, model):
        return model == Pipeline

    def register_url_rules(self, flask_app):
        self.app = flask_app
        flask_app.add_url_rule('/api/pipelines/create', 'create_pipeline', api_key_required(self.create_pipeline), methods=['POST'])
        flask_app.add_url_rule('/api/pipelines/<int:pipeline_id>/start', 'start_pipeline_instance', api_key_required(self.start_pipeline_instance), methods=['POST'])

    def create_pipeline(self):
        json = request.get_json()
        return Response(self._get_pipeline(json), content_type='application/json')

    def start_pipeline_instance_via_reponame(self, repo, json_data=None):
        """
        Start a pipeline_instance identified by the the repo name
        :param repo: VCS repo name or Vcs.repo
        :param json_data: dict for the Data in the PipelineInstance
        :return:
        :rtype PipelineInstance
        """
        vcs = self.ci_module.get_vcs_by_repo_name(repo)
        if vcs is not None:
            if vcs.pipeline_id is not None:
                return self.create_pipeline_instance(vcs.pipeline_id, json_data, vcs_id=vcs.id)
            if vcs.active:
                raise VcsNotFoundException("The repo[{}] did not have a default pipeline defined.".format(repo))
        raise VcsNotFoundException("The repo [{}] is not found in the system".format(repo))

    def start_pipeline_instances_via_pipeline_id(self, pipeline_id, json_data=None):
        for session in get_db_session():
            return self.create_pipeline_instance(pipeline_id, json_data, in_session=session)

    def start_pipeline_instance(self, pipeline_id):
        data = request.get_json()
        return "It worked!" if self.create_pipeline_instance(pipeline_id, data) else "It Failed!"

    def get_pipeline_by_id(self, pipeline_id, session=None):
        if session is None:
            for db_session in get_db_session():
                return db_session.query(Pipeline).get(pipeline_id).serialize()
        else:
            return session.query(Pipeline).get(pipeline_id)

    def get_pipeline_events_by_pipeline_id(self, pipeline_id, session=None):
        if session is None:
            for db_session in get_db_session():
                return [event.serialize() for event in db_session.query(PipelineEvent).filter(PipelineEvent.pipeline_id == pipeline_id).all()]
        else:
            return session.query(PipelineEvent).filter(PipelineEvent.pipeline_id == pipeline_id).all()

    def get_pipeline_instance_by_id(self, pipeline_instance_id, session=None):
        if session is None:
            for db_session in get_db_session():
                return db_session.query(PipelineInstance).get(pipeline_instance_id).serialize()
        else:
            return session.query(PipelineInstance).get(pipeline_instance_id)

    def _get_pipeline(self, json):
        if json:
            for session in get_db_session():
                pipeline = Pipeline(**{"name": json['name'], 'active': json['active']})
                session.add(pipeline)
                session.flush()
                pipeline.stages.extend(self.get_stages(json, pipeline, session))

                response = out_json.dumps(pipeline.serialize())
                try:
                    session.commit()
                finally:
                    if session:
                        session.expunge_all()
                        session.close()
                        session = None

                return response

        raise BaseException("No pipeline was created.")

    def get_actions(self, json, pipeline, workflow, session):
        actions = []
        if 'actions' in json:
            for tmp_action in json['actions']:
                action = Action(**tmp_action)
                action.order = len(actions)
                action.pipeline_id = pipeline.id
                action.workflow_id = workflow.id
                session.add(action)
                actions.append(action)
        return actions

    def get_workflows(self, json, pipeline, stage, session):
        workflows = []
        if 'workflows' in json:
            for tmp_workflow in json['workflows']:
                workflow = Workflow(
                    **{"name": tmp_workflow['name'], 'active': tmp_workflow['active'], "order": len(workflows),
                       "stage_id": stage.id})
                session.add(workflow)
                session.flush()
                workflow.actions.extend(self.get_actions(tmp_workflow, pipeline, workflow, session))
                workflows.append(workflow)
        return workflows

    def get_stages(self, json, pipeline, session):
        stages = []
        if 'stages' in json:
            for tmp_stage in json['stages']:
                stage = Stage(**{"name": tmp_stage['name'], "active": tmp_stage['active'], "order": len(stages),
                                 "pipeline_id": pipeline.id})
                session.add(stage)
                session.flush()
                stage.workflows.extend(self.get_workflows(tmp_stage, pipeline, stage, session))
                stages.append(stage)
        return stages

    def new_alchemy_encoder(self):
        _visited_objs = []

        class AlchemyEncoder(out_json.JSONEncoder):
            def default(self, obj):  # pylint: disable=arguments-differ,method-hidden
                if isinstance(obj.__class__, DeclarativeMeta):
                    # don't re-visit self
                    if obj in _visited_objs:
                        return None
                    _visited_objs.append(obj)

                    # an SQLAlchemy class
                    fields = {}
                    for field in [x for x in dir(obj) if
                                  not x.startswith('_') and x != 'metadata' and x != 'query' and x != 'query_class']:
                        fields[field] = obj.__getattribute__(field)
                    # a json-encodable dict
                    return fields

                return out_json.JSONEncoder.default(self, obj)

        return AlchemyEncoder

    def get_actions_query(self, session, pipeline_id):
        return session.query(Stage, Workflow, Action) \
            .filter(Stage.pipeline_id == pipeline_id) \
            .filter(Stage.id == Workflow.stage_id) \
            .filter(Workflow.id == Action.workflow_id) \
            .order_by(asc(Stage.order)) \
            .order_by(asc(Workflow.id)) \
            .order_by(asc(Action.order))

    def create_pipeline_instance(self, pipeline_id, json_data=None, vcs_id=None, in_session=None):
        if in_session:
            return self._process_pipeline(pipeline_id, vcs_id, json_data, in_session)
        for session in get_db_session():
            return self._process_pipeline(pipeline_id, vcs_id, json_data, session)

    def _process_pipeline(self, pipeline_id, vcs_id, json_data, session):
        pipeline = session.query(Pipeline).get(pipeline_id)
        if pipeline is not None and pipeline.active:
            pipeline_instance = PipelineInstance(pipeline_id=pipeline_id, status_id=StatusConstants.INPROGRESS,
                                                 created_date=datetime.datetime.utcnow(),
                                                 start_date=datetime.datetime.utcnow())
            session.add(pipeline_instance)
            session.flush()
            self._setup_pipeline(session, pipeline_id, pipeline_instance.id)
            try:
                if json_data and 'parameters' in json_data:
                    for parameter, value in json_data['parameters'].items():
                        tmp = PipelineParameters(parameter=parameter, value=value)
                        tmp.pipeline_instance_id = pipeline_instance.id
                        session.add(tmp)

                        if parameter == "commit":
                            # Look for vcs and get the ID
                            if vcs_id is None:
                                vcs = self.ci_module.get_vcs_by_pipeline_id(pipeline_id, session=session)
                                vcs_id = vcs.id if vcs is not None else None
                            else:
                                self.ci_module.create_git_commit(value, vcs_id, pipeline_instance_id=pipeline_instance.id, session=session)

            except Exception as exception:
                logger.error("Creating Pipeline Instance failed.")
                logger.error(exception)

            session.commit()
            create_pipeline_instance = pipeline_instance.serialize()
            return create_pipeline_instance
        try:
            logger.info("Inactive pipeline: {}".format(pipeline.name))
        except AttributeError:
            pass
        return {"message": "Invalid Pipeline, or inactive pipeline"}

    def cancel_pipeline_instance(self, pipeline_instance_id):
        for session in get_db_session():
            pipeline_instance = self.get_pipeline_instance_by_id(pipeline_instance_id, session)
            if pipeline_instance:
                for action_instance in pipeline_instance.action_instances:
                    for client in StoreService.get_clients(self.app).values():
                        if action_instance.status_id <= StatusConstants.SUCCESS and client.get_uri() == action_instance.assigned_to:
                            self.queue_constants.cancel_worker(action_instance.serialize())
                pipeline_instance.status_id = StatusConstants.CANCELED
                pipeline_instance.end_date = datetime.datetime.utcnow()
                session.commit()
            else:
                raise InvalidObjectException("Pipeline Instance not found", 404)
        return {"message": "Running clients have been canceled and pipeline canceled."}

    def _setup_pipeline(self, session, pipeline_id, pipeline_instance_id):
        current_stage = None
        current_workflow = None
        first_action_instance = True
        added_objects = []
        for (stage, workflow, action) in self.get_actions_query(session, pipeline_id):
            if current_stage is None:
                current_stage = stage.convert_to_instance()
                current_stage.pipeline_instance_id = pipeline_instance_id
                session.add(current_stage)
                session.flush()
                added_objects.append(current_stage)
            elif current_stage.stage_id != stage.id:
                break

            if current_workflow is None or current_workflow.workflow_id != workflow.id:
                first_action_instance = True
                current_workflow = workflow.convert_to_instance()
                current_workflow.stage_instance_id = current_stage.id
                session.add(current_workflow)
                session.flush()
                added_objects.append(current_workflow)

            slices = max(1, action.slices)

            for slice_num in range(slices):
                action_instance = action.convert_to_instance()
                action_instance.workflow_instance_id = current_workflow.id
                action_instance.pipeline_instance_id = pipeline_instance_id
                action_instance.slice = "{}/{}".format(slice_num + 1, slices)

                if first_action_instance:
                    action_instance.status_id = StatusConstants.READY

                session.add(action_instance)
                added_objects.append(action_instance)

            session.flush()

            if first_action_instance:
                first_action_instance = False
        return added_objects
