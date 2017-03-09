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
from rapid.workflow.WorkflowService import WorkflowService

try:
    import simplejson as json
except:
    import json

import re
import logging
import datetime
from flask import Response, request
from sqlalchemy.orm import subqueryload, joinedload
from sqlalchemy import desc, asc
from sqlalchemy.orm.util import join
from sqlalchemy.sql.sqltypes import DATETIME

from rapid.lib import json_response
from rapid.lib.Utils import ORMUtil
from rapid.lib.modules.modules import QaModule

from rapid.lib import api_key_required
from rapid.lib.Constants import ModuleConstants
from rapid.lib.WorkRequest import WorkRequestEncoder
from rapid.lib.framework.Injectable import Injectable
from rapid.master.data.database.dal import get_dal
from rapid.workflow.ActionInstanceService import ActionInstanceService
from rapid.workflow.QueueService import QueueService

logger = logging.getLogger("rapid")


class APIRouter(Injectable):
    __injectables__ = {'action_instance_service': ActionInstanceService,
                       'queue_service': QueueService,
                       ModuleConstants.QA_MODULE: None,
                       'workflow_service': WorkflowService}
    classes, models, table_names = None, None, None
    class_map = {}

    def __init__(self, action_instance_service, queue_service, qa_module, workflow_service):
        """

        :param action_instance_service:
        :type action_instance_service:
        :param queue_service:
        :type queue_service:
        :param qa_module:
        :type qa_module: QaModule
        :param workflow_service:
        :type workflow_service: WorkflowService
        """
        self.app = None
        self.action_instance_service = action_instance_service
        self.queue_service = queue_service
        self.qa_module = qa_module
        self.workflow_service = workflow_service

    def register_url_rules(self, flask_app):
        flask_app.add_url_rule('/api/<path:endpoint>', 'api_list', api_key_required(self.list), methods=['GET'])
        flask_app.add_url_rule('/api/<path:endpoint>/metadata', 'api_meta', api_key_required(self.metadata), methods=['GET'])
        flask_app.add_url_rule('/api/metadata', 'all_api_meta', api_key_required(self.metadata), methods=['GET'])
        flask_app.add_url_rule('/api/bulk_create', 'bulk_create', api_key_required(self.bulk_create), methods=['PUT'])
        flask_app.add_url_rule('/api/<path:endpoint>', 'create_object', api_key_required(self.create), methods=['PUT'])
        flask_app.add_url_rule('/api/<path:endpoint>/<int:id>', 'edit_object', api_key_required(self.edit_object), methods=['POST'])
        flask_app.add_url_rule('/api/<path:endpoint>/<int:id>', 'delete_object', api_key_required(self.delete_object), methods=['DELETE'])
        flask_app.add_url_rule('/api/<path:endpoint>/<int:id>', 'list_object', api_key_required(self.list_single_object), methods=['GET'])
        flask_app.add_url_rule('/api/action_instances/<int:id>/done', 'finish_action_instance', api_key_required(self.finish_action_instance), methods=['POST'])
        flask_app.add_url_rule('/api/action_instances/<int:id>/callback', 'callback_action_instance', api_key_required(self.callback_action_instance), methods=['POST'])
        flask_app.add_url_rule('/api/action_instances/<int:id>/reset', 'reset_action_instance', api_key_required(self.reset_action_instance), methods=['POST'])
        flask_app.add_url_rule('/api/action_instances/<int:id>/results', 'action_instance_results', api_key_required(self.action_instance_results), methods=['GET'])
        flask_app.add_url_rule('/api/pipeline_instances/<int:id>/failure_count', 'failure_count_instance', api_key_required(self.failure_count_instance))
        flask_app.add_url_rule('/api/queue', 'get_queue', api_key_required(self.get_queue), methods=['GET'])
        flask_app.add_url_rule('/api/pipeline_instances/<int:id>/reset', 'reset_pipeline_instance', api_key_required(self.reset_pipeline_instance), methods=['POST', 'GET'])

        flask_app.add_url_rule("/api/reports/canned/<path:report_name>", 'canned_report', api_key_required(self.canned_report), methods=['GET'])
        flask_app.add_url_rule("/api/reports/canned/list", 'list_canned_report', api_key_required(self.list_canned_reports), methods=['GET'])

        self.app = flask_app

    def reset_pipeline_instance(self, id):
        response = self.action_instance_service.reset_pipeline_instance(id)
        return Response(json.dumps({'message': ('Success!' if response else 'Failure!')}), content_type='application/json', status=(200 if response else 500))

    def get_queue(self):
        return Response(json.dumps(self.queue_service.get_current_work(), cls=WorkRequestEncoder), content_type='application/json')

    def failure_count_instance(self, id):
        pass

    def action_instance_results(self, id):
        filter = None
        try:
            filter = request.args['filter']
        except:
            pass

        return Response(json.dumps(self.qa_module.get_test_results(id, filter)), content_type='application/json')

    def list_single_object(self, endpoint, id):
        if self._is_valid(endpoint):
            session = self.app.db.session()
            try:
                clazz = self.class_map[endpoint]
                query = session.query(clazz).filter(clazz.id == id)
                allowed_fields = self._get_additional_fields(clazz)
                instance = query.one()
                return Response(json.dumps(instance.serialize(allowed_children=allowed_fields)), content_type='application/json')
            finally:
                if session:
                    session.close()
                    session = None

    def list(self, endpoint):
        if self._is_valid(endpoint):
            session = self.app.db.session()
            try:
                clazz = self._get_clazz(endpoint)
                results = []
                query = self._get_query(session, clazz)
                query = self._set_filter(clazz, query)
                query = self._set_orderby_direction(query, clazz)
                query = self._set_joins(query)
                query = self._set_limit(query)
                fields = self._get_additional_fields(clazz)
                results = []
                for result in query.all():
                    results.append(result.serialize(fields))
                return Response(json.dumps(results), content_type='application/json')
            finally:
                if session:
                    session.close()
                    session = None
        else:
            return Response(status=404)

    def _get_clazz(self, endpoint):
        return self.class_map[endpoint]

    @staticmethod
    def _get_query(session, clazz):
        return session.query(clazz)

    def _set_filter(self, clazz, query):
        filter = request.args['filter'] if 'filter' in request.args else None
        return ORMUtil.get_filtered_query(query, filter, clazz)

    def _set_joins(self, query):
        if 'joins' in request.args:
            if 'orderby' not in request.args:
                raise Exception("You can't join with out an orderby")
            current_attribute = None
            queries = []
            for join in request.args['joins'].split(';'):
                split = join.split('=')
                attribute = split[0]

                if attribute.startswith('_'):  # If attribute starts with '_' then it is a root attribute, start from here.
                    current_attribute = None
                    attribute = attribute.split('_', 1)[1]

                if current_attribute is None:
                    current_attribute = attribute
                else:
                    current_attribute = "{}.{}".format(current_attribute, attribute)

                queries.append(joinedload(current_attribute))

                if len(split) > 1:
                    for field in split[1].split(','):
                        queries.append(joinedload("{}.{}".format(current_attribute, field)))
            query = query.options(queries)
        return query

    def _set_orderby_direction(self, query, clazz):
        if 'orderby' in request.args:
            map = {'desc': desc, 'asc': asc}
            for orderby in request.args['orderby'].split(','):
                try:
                    column, order = orderby.split(':')
                    if hasattr(clazz, column):
                        column = getattr(clazz, column)
                        __import__(clazz.__module__, fromlist=[clazz.__class__])
                    query = query.order_by(map[order](column))
                except:
                    import traceback
                    traceback.print_exc()
                    pass
        return query

    def _get_additional_fields(self, clazz, fields=None):
        fields = {clazz.__tablename__: []} if fields is None else fields
        try:
            for tmp_string in request.args['fields'].split(';'):
                relation_split = tmp_string.split('=')
                if len(relation_split) == 1:
                    for field in relation_split[0].split(','):
                        fields[clazz.__tablename__].append(field)
                else:
                    table_name = relation_split[0]
                    for field in relation_split[1].split(','):
                        try:
                            fields[table_name].append(field)
                        except:
                            fields[table_name] = []
                            fields[table_name].append(field)
        except:
            pass
        return fields

    def _set_limit(self, query):
        limit = 100
        if 'limit' in request.args:
            try:
                limit = min(limit, int(request.args['limit']))
            except:
                pass
        return query.limit(limit + 1)

    def bulk_create(self):
        result = {}
        for (endpoint, objects) in request.get_json().items():
            if self._is_valid(endpoint):
                clazz = self.class_map[endpoint]
                result[endpoint] = []
                for object in objects:
                    result[endpoint].append(self._create_from_request(clazz, object))
        return Response(json.dumps(result), content_type="application/json")

    def create(self, endpoint):
        if self._is_valid(endpoint):
            clazz = self.class_map[endpoint]
            return Response(json.dumps(self._create_from_request(clazz, request.get_json())))
        return Response(status=404)

    def edit_object(self, endpoint, id):
        if self._is_valid(endpoint):
            clazz = self.class_map[endpoint]
            session = self.app.db.session()
            try:
                dal = self._retrieve_dal(clazz)
                instance = dal.edit_object(session, clazz, id, request.json)
                return Response(json.dumps(instance.serialize()), content_type='application/json')
            finally:
                if session:
                    session.close()
                    session = None
        return Response(status=404)

    def delete_object(self, endpoint, id):
        if self._is_valid(endpoint):
            clazz = self.class_map[endpoint]
            session = self.app.db.session()
            try:
                dal = self._retrieve_dal(clazz)
                instance = dal.delete_object(session, clazz, id)
                return Response(json.dumps(instance.serialize()), content_type='application/json')
            finally:
                if session:
                    session.close()
                    session = None
        return Response(status=404)

    def reset_action_instance(self, id):
        try:
            if self.action_instance_service.reset_action_instance(id, True):
                return Response(json.dumps({"message": "Action instance reset"}), content_type='application/json')
            return Response(json.dumps({"message": "Unable to reset instance"}), content_type='application/json', status=505)
        except Exception as exception:
            logger.error(exception)

        return Response(json.dumps({"message": "Something was wrong"}), content_type='application/json', status=500)

    def callback_action_instance(self, id):
        return Response(json.dumps(self.action_instance_service.callback(id, request.get_json())), content_type='application/json')

    def finish_action_instance(self, id):
        try:
            return Response(json.dumps(self.action_instance_service.finish_action_instance(id, request.get_json())))
        except Exception as exception:
            logger.error(exception)
            return Response("Something went wrong!", status=500)

    def metadata(self, endpoint=None):
        if self._is_valid(endpoint):
            clazz = self.class_map[endpoint]
            return Response(json.dumps(self._explode_class(clazz)), content_type="application/json")
        else:
            ret_map = {}
            for key in self.class_map.keys():
                clazz = self.class_map[key]
                ret_map[key] = self._explode_class(clazz)
                ret_map[key]['url'] = "/api/{}/metadata".format(key)
            return Response(json.dumps(ret_map), content_type="application/json")

    @json_response()
    def canned_report(self, report_name):
        return self.workflow_service.get_custom_report(report_name)

    @json_response()
    def list_canned_reports(self):
        return self.workflow_service.list_canned_reports()

    def _explode_class(self, clazz):
        columns = {}
        for column in clazz.__table__._columns:
            columns[column.name] = column.type.__class__.__name__

        for field in clazz().__relationships__():
            columns[field] = "__ON_REQUEST__"

        return columns

    def _is_valid(self, endpoint):
        return endpoint in self._get_models()

    def _get_models(self):
        if self.models is None:
            self._load_objects()

        return self.models

    def _load_objects(self):
        self.classes = []
        self.models = []
        self.table_names = []

        for clazz in self.app.db.Model._decl_class_registry.values():
            try:
                self.table_names.append(clazz.__tablename__)
                self.classes.append(clazz)
            except:
                pass
        for table in self.app.db.metadata.tables.items():
            if table[0] in self.table_names:
                clazz = self.classes[self.table_names.index(table[0])]
                name = clazz.__tablename__.lower()
                self.models.append(name)
                self.class_map[name] = clazz

    def _retrieve_dal(self, clazz):
        dal = get_dal(clazz)
        if dal is None:
            raise Exception("Object not found.")
        return dal

    def _create_from_request(self, clazz, json):
        session = self.app.db.session()
        try:
            dal = self._retrieve_dal(clazz)
            return dal.create_object(session, clazz, json)
        except Exception as exception:
            logger.error(exception)
            raise exception
        finally:
            if session:
                session.close()
                session = None

    @staticmethod
    def _convert_to_dict(row):
        ret_dict = {}
        for column in row.__table__.columns:
            ret_dict[column.name] = str(getattr(row, column.name))
        return ret_dict
