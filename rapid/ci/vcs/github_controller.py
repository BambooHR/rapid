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
import logging

from functools import wraps

from flask import Flask
from flask.globals import request
from flask.wrappers import Response

from rapid.master.master_configuration import MasterConfiguration
from rapid.ci.data.github_dal import GithubHelper
from rapid.lib import json_response, HttpException
from rapid.lib.framework.injectable import Injectable
from rapid.lib.modules import WorkflowModule

logger = logging.getLogger("rapid")


class GithubController(Injectable):

    def __init__(self, github_helper: GithubHelper, rapid_config: MasterConfiguration, workflow_module: WorkflowModule):
        self.github_helper = github_helper
        self.rapid_config = rapid_config
        self.workflow_module = workflow_module

    def register_url_rules(self, flask_app):
        flask_app.add_url_rule("/api/github/webhooks", "github_webooks", self._github_check_wrapper(self.process_webhooks), methods=["POST"])
        flask_app.add_url_rule("/api/github/webhooks/<path:pipeline_id>", "github_webook_pipeline", self._github_check_wrapper(self.process_webhooks_pipeline), methods=['POST'])

    def _github_check_wrapper(self, func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if 'X-Hub-Signature' in request.headers \
                    and GithubHelper.is_valid_request(request.headers['X-Hub-Signature'], self.rapid_config.github_webhooks_key, request.data):
                return func(*args, **kwargs)
            return Response("Not authorized", status=401)
        return decorated_view

    def __process_request(self):
        request_json = request.get_json()
        return request_json

    @json_response()
    def process_webhooks_pipeline(self, pipeline_id):
        request_json = self.__process_request()
        pipeline_instance = self.workflow_module.start_pipeline_by_id(pipeline_id, self._build_request_parameters(request_json))

        if pipeline_instance:
            return pipeline_instance

        raise HttpException({'message': 'Something went wrong'}, code=500)

    @json_response()
    def process_webhooks(self):
        # perform operation
        request_json = self.__process_request()

        pipeline_instance = self.workflow_module.start_pipeline_via_repo(request_json['repository']['clone_url'],
                                                                         self._build_request_parameters(request_json))

        if pipeline_instance:
            return pipeline_instance
        raise HttpException({'message': 'Something went wrong'}, code=500)

    def _build_request_parameters(self, request_json):
        parameters = {'branch': GithubHelper.get_branch_from_ref(request_json['ref']) if 'ref' in request_json else None}
        parameters.update(self._load_default_parameters(request_json))

        return {'parameters': parameters}

    def _load_default_parameters(self, request_json):
        parameters = {}
        if self.rapid_config and self.rapid_config.github_default_parameters is not None:
            for parameter_string in self.rapid_config.github_default_parameters.split('\n'):
                try:
                    tmp = parameter_string.strip().split(':')
                    parameter = tmp[0]
                    key = tmp[1]
                    value = self._get_json_value(request_json, key)
                    if parameter and value:
                        parameters[parameter] = self._get_json_value(request_json, key)
                except Exception:  # pylint: disable=broad-except
                    pass
        return parameters

    def _get_json_value(self, request_json, key):
        if '.' in key:
            tmp = key.split('.', 1)
            if tmp[0] in request_json:
                return self._get_json_value(request_json[tmp[0]], tmp[1])
            return None

        return request_json[key] if key in request_json else None
