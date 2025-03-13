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
# pylint: disable=broad-except,too-many-public-methods
import logging
from typing import Dict, List, Tuple

from flask_sqlalchemy.query import Query

from rapid.workflow.fields_parser import FieldsParser

try:
    import simplejson as json
except ImportError:
    import json


from werkzeug.exceptions import BadRequestKeyError
from sqlalchemy.orm import joinedload
from sqlalchemy import desc, asc
from flask import Response

from rapid.lib.http_wrapper import HTTPWrapper
from rapid.lib.constants import Constants
from rapid.lib.modules import QaModule
from rapid.lib import json_response, api_key_required, get_declarative_base, get_db_session
from rapid.lib.utils import ORMUtil, RoutingUtil
from rapid.lib.store_service import StoreService
from rapid.lib.version import Version
from rapid.lib.work_request import WorkRequestEncoder
from rapid.lib.framework.injectable import Injectable
from rapid.master.data.database.dal import get_dal
from rapid.release.release_service import ReleaseService
from rapid.workflow.action_instances_service import ActionInstanceService
from rapid.workflow.queue_service import QueueService
from rapid.workflow.workflow_service import WorkflowService

logger = logging.getLogger("rapid")


class APIRouter(Injectable):
    classes, models, table_names = None, None, None
    class_map = {}

    def __init__(self, action_instance_service: ActionInstanceService,
                 queue_service: QueueService,
                 qa_module: QaModule,
                 workflow_service: WorkflowService,
                 release_service: ReleaseService,
                 http_wrapper: HTTPWrapper):
        self.app = None
        self.action_instance_service = action_instance_service
        self.queue_service = queue_service
        self.qa_module = qa_module
        self.workflow_service = workflow_service
        self.release_service = release_service
        self.http_wrapper = http_wrapper

    def register_url_rules(self, flask_app):
        flask_app.add_url_rule('/api/<path:endpoint>', 'api_list', api_key_required(self.list), methods=['GET', 'POST'])
        flask_app.add_url_rule('/api/<path:endpoint>/metadata', 'api_meta', api_key_required(self.metadata), methods=['GET'])
        flask_app.add_url_rule('/api/metadata', 'all_api_meta', api_key_required(self.metadata), methods=['GET'])
        flask_app.add_url_rule('/api/bulk_create', 'bulk_create', api_key_required(self.bulk_create), methods=['PUT'])
        flask_app.add_url_rule('/api/<path:endpoint>', 'create_object', api_key_required(self.create), methods=['PUT'])
        flask_app.add_url_rule('/api/<path:endpoint>/<int:_id>', 'edit_object', api_key_required(self.edit_object), methods=['POST'])
        flask_app.add_url_rule('/api/<path:endpoint>/<int:_id>', 'delete_object', api_key_required(self.delete_object), methods=['DELETE'])
        flask_app.add_url_rule('/api/<path:endpoint>/<int:_id>', 'list_object', api_key_required(self.list_single_object), methods=['GET'])
        flask_app.add_url_rule('/api/action_instances/<int:_id>/done', 'finish_action_instance', api_key_required(self.finish_action_instance), methods=['POST'])
        flask_app.add_url_rule('/api/action_instances/<int:_id>/callback', 'callback_action_instance', api_key_required(self.callback_action_instance), methods=['POST'])
        flask_app.add_url_rule('/api/action_instances/<int:_id>/reset', 'reset_action_instance', api_key_required(self.reset_action_instance), methods=['POST'])
        flask_app.add_url_rule('/api/action_instances/<int:_id>/results', 'action_instance_results', api_key_required(self.action_instance_results), methods=['GET'])
        flask_app.add_url_rule('/api/action_instances/<int:action_instance_id>/work_request', 'action_instance_work_request', api_key_required(self.action_instance_work_request), methods=['GET'])

        flask_app.add_url_rule('/api/action_instances/<int:action_instance_id>/is_completing', 'action_instance_is_completing', api_key_required(self.action_instance_is_completing), methods=['GET'])
        flask_app.add_url_rule('/api/action_instances/<int:action_instance_id>/clear_completing', 'action_instance_clear_completing', api_key_required(self.action_instance_clear_completing), methods=['GET'])

        flask_app.add_url_rule('/api/pipeline_instances/<int:_id>/failure_count', 'failure_count_instance', api_key_required(self.failure_count_instance))
        flask_app.add_url_rule('/api/queue', 'get_queue', api_key_required(self.get_queue), methods=['GET'])
        flask_app.add_url_rule('/api/pipeline_instances/<int:_id>/reset', 'reset_pipeline_instance', api_key_required(self.reset_pipeline_instance), methods=['POST', 'GET'])

        flask_app.add_url_rule("/api/reports/canned/<path:report_name>", 'canned_report', api_key_required(self.canned_report), methods=['GET'])
        flask_app.add_url_rule("/api/reports/canned/list", 'list_canned_report', api_key_required(self.list_canned_reports), methods=['GET'])

        flask_app.add_url_rule("/api/pipeline_instances/<int:pipeline_instance_id>/cancel", "cancel_pipeline_instance", api_key_required(self.cancel_pipeline_instance), methods=['POST'])
        flask_app.add_url_rule("/api/action_instances/<int:action_instance_id>/cancel", "cancel_action_instance", api_key_required(self.cancel_action_instance), methods=['POST'])
        flask_app.add_url_rule("/api/pipeline_instances/<int:pipeline_instance_id>/print", "print_pipeline_instance", api_key_required(self.print_pipeline_instance), methods=['GET'])

        flask_app.add_url_rule("/api/canary", "canary_endpoint", self.get_canary, methods=['GET'])

        self.app = flask_app

    def _get_args(self):
        try:
            if self.http_wrapper.current_request().content_type == 'application/json':
                return self.http_wrapper.current_request().get_json()
        except Exception:
            pass
        return self.http_wrapper.current_request().args

    def reset_pipeline_instance(self, _id):
        response = self.action_instance_service.reset_pipeline_instance(_id)
        return Response(json.dumps({'message': ('Success!' if response else 'Failure!')}), content_type='application/json', status=(200 if response else 500))

    def get_queue(self):
        return Response(json.dumps(self.queue_service.get_current_work(), cls=WorkRequestEncoder), content_type='application/json')

    def failure_count_instance(self, _id):
        pass

    def action_instance_results(self, _id):
        _filter = None
        try:
            _filter = self._get_args()['filter']
        except (KeyError, TypeError):
            pass

        return Response(json.dumps(self.qa_module.get_test_results(_id, _filter)), content_type='application/json')

    def list_single_object(self, endpoint, _id):
        if self._is_valid(endpoint):
            for session in get_db_session():
                clazz = self.class_map[endpoint]
                query = session.query(clazz).filter(clazz.id == _id)
                allowed_fields, query = self._get_additional_fields(clazz, query)
                instance = query.one()
                return Response(json.dumps(instance.serialize(allowed_children=allowed_fields)), content_type='application/json')
        return Response("Not Valid", status=404)

    def _get_cursor(self) -> int:
        cursor = None

        try:
            # Check the headers first, use that if set.
            header = self.http_wrapper.current_request().headers.get(Constants.CONTINUATION_HEADER, None)
            if header:
                cursor = header
            else:
                _json = self.http_wrapper.current_request().get_json(silent=True)
                if _json is not None:
                    cursor = _json['continuation_token'] if 'continuation_token' in _json else None
                else:
                    cursor = self._get_args()['continuation_token']

        except (KeyError, TypeError, AttributeError, ValueError):
            pass

        if cursor:
            return self._de_obfuscate_id(cursor)
        return -1

    def _de_obfuscate_id(self, cursor: str) -> int:
        return RoutingUtil.deobfuscate_id(cursor)

    def _set_cursor(self, query, clazz):
        cursor = self._get_cursor()
        if cursor > -1:
            query = query.filter(clazz.id > cursor)
        return query

    def _get_pagination_header(self, results: list, limit: int) -> dict:
        if results and len(results) == limit:
            return {Constants.CONTINUATION_HEADER: RoutingUtil.obfuscate_id(results[-1]['id'])}
        return {}

    def list(self, endpoint, version2: bool = False, version_obj = None):
        if self._is_valid(endpoint):
            for session in get_db_session():
                query_limit = self._get_limit()
                clazz = self._get_clazz(endpoint)
                query = self._get_query(session, clazz)
                query = self._set_filter(clazz, query)
                query = self._set_orderby_direction(query, clazz)
                query = self._set_joins(query)
                query = self._set_cursor(query, clazz)
                query = query.limit(query_limit)
                fields, query = self._get_additional_fields(clazz, query)

                results = []
                for result in query.all():
                    results.append(result.serialize(fields))
                return Response(json.dumps(results), content_type='application/json', headers=self._get_pagination_header(results, query_limit))
        else:
            return Response(status=404)

    @json_response()
    def cancel_pipeline_instance(self, pipeline_instance_id):
        return self.workflow_service.cancel_pipeline_instance(pipeline_instance_id)

    @json_response()
    def cancel_action_instance(self, action_instance_id):
        return self.workflow_service.cancel_action_instance(action_instance_id)

    @json_response()
    def action_instance_work_request(self, action_instance_id):
        return self.workflow_service.get_work_request_by_action_instance_id(action_instance_id)

    def _get_clazz(self, endpoint):
        return self.class_map[endpoint]

    @staticmethod
    def _get_query(session, clazz):
        return session.query(clazz)

    def _set_filter(self, clazz, query):
        _filter = self._get_args()['filter'] if 'filter' in self._get_args() else None
        return ORMUtil.get_filtered_query(query, _filter, clazz)

    def _set_joins(self, query):
        if 'joins' in self._get_args():
            if 'orderby' not in self._get_args():
                raise Exception("You can't join with out an orderby")
            current_attribute = None
            queries = []
            for join in self._get_args()['joins'].split(';'):
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
        if 'orderby' in self._get_args():
            _map = {'desc': desc, 'asc': asc}
            for orderby in self._get_args()['orderby'].split(','):
                try:
                    column, order = orderby.split(':')
                    if hasattr(clazz, column):
                        column = getattr(clazz, column)
                        __import__(clazz.__module__, fromlist=[clazz.__class__])
                    query = query.order_by(_map[order](column))
                except Exception:
                    import traceback
                    traceback.print_exc()
        return query

    def _process_single_field(self, clazz, field, mapping: Dict):
        try:
            attr = getattr(clazz, field)
            mapping[field] = attr.mapper.class_
        except:
            ...

    def _get_additional_fields(self, clazz, query: Query)->Tuple[Dict[str, List[str]], Query]:
        args = self._get_args()
        parser = FieldsParser(clazz, args['fields'] if args and 'fields' in args else '')
        field_joins = parser.field_joins()
        if field_joins:
            query = query.options(*field_joins)
        return parser.fields_mapping(), query

    def _get_additional_fields_legacy(self, clazz, query, fields=None):
        fields = {clazz.__tablename__: []} if fields is None else fields
        _mappings = {}
        try:
            _field_loads = {}
            _current_load = None
            for tmp_string in self._get_args()['fields'].split(';'):
                relation_split = tmp_string.split('=')
                if len(relation_split) == 1:
                    for field in relation_split[0].split(','):
                        if field:
                            self._process_single_field(clazz, field, _mappings)
                            if _mappings[field] not in _field_loads:
                                _field_loads[_mappings[field]] = joinedload(getattr(clazz, field))
                            else:
                                _field_loads[_mappings[field]].joinedload(getattr(clazz, field))
                            fields[clazz.__tablename__].append(field)
                else:
                    table_name = relation_split[0]
                    field_cls = _mappings[table_name]
                    for field in relation_split[1].split(','):
                        self._process_single_field(field_cls, field, _mappings)
                        try:
                            if table_name in _mappings:
                                if field_cls in _field_loads:
                                    _joined = _field_loads[field_cls].joinedload(getattr(field_cls, field))
                                    _field_loads[_mappings[field]] = _joined
                            fields[table_name].append(field)
                        except (AttributeError, TypeError, KeyError):
                            fields[table_name] = []
                            fields[table_name].append(field)
                if _field_loads:
                    query = query.options(list(_field_loads.values()))
        except Exception:
            pass
        return fields

    def _get_limit(self) -> int:
        try:
            return int(self._get_args()['limit'])
        except (AttributeError, TypeError, ValueError, BadRequestKeyError, KeyError):
            return 100

    def bulk_create(self):
        result = {}
        for (endpoint, objects) in self.http_wrapper.current_request().get_json().items():
            if self._is_valid(endpoint):
                clazz = self.class_map[endpoint]
                result[endpoint] = []
                for _object in objects:
                    result[endpoint].append(self._create_from_request(clazz, _object))
        return Response(json.dumps(result), content_type="application/json")

    def create(self, endpoint):
        if self._is_valid(endpoint):
            clazz = self.class_map[endpoint]
            return Response(json.dumps(self._create_from_request(clazz, self.http_wrapper.current_request().get_json())), content_type="application/json")
        return Response(status=404)

    def edit_object(self, endpoint, _id):
        if self._is_valid(endpoint):
            clazz = self.class_map[endpoint]
            for session in get_db_session():
                dal = self._retrieve_dal(clazz)
                instance = dal.edit_object(session, clazz, _id, self.http_wrapper.current_request().json)
                return Response(json.dumps(instance.serialize()), content_type='application/json')
        return Response(status=404)

    def delete_object(self, endpoint, _id):
        if self._is_valid(endpoint):
            clazz = self.class_map[endpoint]
            for session in get_db_session():
                dal = self._retrieve_dal(clazz)
                instance = dal.delete_object(session, clazz, _id)
                return Response(json.dumps(instance.serialize()), content_type='application/json')
        return Response(status=404)

    def reset_action_instance(self, _id):
        try:
            _json = self.http_wrapper.current_request().get_json(silent=True)
            if self.action_instance_service.reset_action_instance(_id, _json['complete_reset'] if _json and 'complete_reset' in _json else False):
                return Response(json.dumps({"message": "Action instance reset"}), content_type='application/json')
            return Response(json.dumps({"message": "Unable to reset instance"}), content_type='application/json', status=505)
        except Exception as exception:
            logger.error(exception)

        return Response(json.dumps({"message": "Something was wrong"}), content_type='application/json', status=500)

    def callback_action_instance(self, _id):
        return Response(json.dumps(self.action_instance_service.callback(_id, self.http_wrapper.current_request().get_json())), content_type='application/json')

    def finish_action_instance(self, _id):
        try:
            return Response(json.dumps(self.action_instance_service.finish_action_instance(_id, self.http_wrapper.current_request().get_json())), content_type='application/json')
        except Exception as exception:
            logger.error(exception)
            return Response("Something went wrong!", status=500)

    def metadata(self, endpoint=None):
        if self._is_valid(endpoint):
            clazz = self.class_map[endpoint]
            return Response(json.dumps(self._explode_class(clazz)), content_type="application/json")
        
        ret_map = {}
        for key, clazz in self.class_map.items():
            ret_map[key] = self._explode_class(clazz)
            ret_map[key]['url'] = "/api/{}/metadata".format(key)
        return Response(json.dumps(ret_map), content_type="application/json")

    @json_response()
    def canned_report(self, report_name):
        return self.workflow_service.get_custom_report(report_name)

    @json_response()
    def list_canned_reports(self):
        return self.workflow_service.list_canned_reports()

    @json_response()
    def action_instance_is_completing(self, action_instance_id):
        return {"status": StoreService.is_completing(action_instance_id)}

    @json_response()
    def action_instance_clear_completing(self, action_instance_id):
        return {"status": StoreService.clear_completing(action_instance_id)}

    @json_response()
    def print_pipeline_instance(self, pipeline_instance_id):
        pipeline_instance = self.workflow_service.get_pipeline_instance_by_id(pipeline_instance_id)
        response = ""
        response = "pipeline: {}, Status: {}, Start Date: {}, End Date:{}\n".format(pipeline_instance.id, pipeline_instance.status_id, pipeline_instance.start_date, pipeline_instance.end_date)
        for stage_instance in pipeline_instance.stage_instances:
            response += "stage: {}, Status: {}, Start Date: {}, End Date: {}\n".format(stage_instance.id, stage_instance.status_id, stage_instance.start_date, stage_instance.end_date)
            for workflow_instance in stage_instance.workflow_instances:
                response += "  workflow: {}, Status: {}, Start Date: {}, End Date: {}\n".format(workflow_instance.id, workflow_instance.status_id, workflow_instance.start_date, workflow_instance.end_date)
                for action_instance in workflow_instance.action_instances:
                    response += "    action: {}, Status: {}, Start Date: {}, End Date: {}, Order: {}, Slice: {}\n".format(action_instance.id, action_instance.status_id, action_instance.start_date, action_instance.end_date, action_instance.order, action_instance.slice)
        return {"message": response}

    @json_response()
    def get_canary(self):
        return {'version': Version.get_version()}

    def _explode_class(self, clazz):
        columns = {}
        for column in clazz.__table__._columns:  # pylint: disable=protected-access
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

        _base = get_declarative_base()
        registry = _base.registry._class_registry if hasattr(_base, 'registry') else _base._decl_class_registry
        for clazz in list(registry.values()):  # pylint: disable=protected-access
            try:
                self.table_names.append(clazz.__tablename__)
                self.classes.append(clazz)
            except Exception:
                pass
        for table in _base.metadata.tables.items():
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

    def _create_from_request(self, clazz, _json):
        for session in get_db_session():
            dal = self._retrieve_dal(clazz)
            return dal.create_object(session, clazz, _json)

    @staticmethod
    def _convert_to_dict(row):
        ret_dict = {}
        for column in row.__table__.columns:
            ret_dict[column.name] = str(getattr(row, column.name))
        return ret_dict
