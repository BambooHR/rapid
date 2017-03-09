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

try:
    import simplejson as json
except:
    import json

from functools import wraps

from flask.globals import request
from flask.wrappers import Response

from rapid.ci.data.GithubDal import GithubHelper
from rapid.ci.services.GithubService import GithubService
from rapid.lib.Constants import ModuleConstants
from rapid.lib.framework.Injectable import Injectable
from rapid.lib.modules.modules import WorkflowModule
import logging

logger = logging.getLogger("rapid")


class GithubController(Injectable):
    __injectables__ = {'github_service': GithubService,
                       'github_helper': GithubHelper,
                       ModuleConstants.WORKFLOW_MODULE: WorkflowModule,
                       'rapid_config': 'rapid_config'}

    def __init__(self, github_service, github_helper, rapid_config, workflow_module, flask_app):
        """

        :param github_service:
        :type github_service: GithubService
        :param github_helper:
        :type github_helper: GithubHelper
        :param rapid_config:
        :type rapid_config: master.MasterConfiguration.MasterConfiguration
        :param workflow_module:
        :type workflow_module: WorkflowModule
        :param flask_app:
        :type flask_app: flask.app.Flask
        """
        self.flask_app = flask_app
        self.github_service = github_service
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
            else:
                return Response("Not authorized", status=401)
        return decorated_view

    def __process_request(self):
        request_json = request.get_json()
        try:
            pass
            # self.github_helper.record_status({
            #     "pull_request_repo": request_json['repository']['full_name'],
            #     "status": "pending",
            #     "description": "Queued",
            #     "type": "build"
            # }, request_json['head_commit']['id'])
        except Exception as exception:
            logger.error(exception)
        return request_json

    def process_webhooks_pipeline(self, pipeline_id):
        request_json = self.__process_request()
        pipeline_instance = self.workflow_module.start_pipeline_by_id(pipeline_id, self._build_request_parameters(request_json))

        if pipeline_instance:
            return Response(json.dumps(pipeline_instance), content_type="application/json")
        else:
            return Response(json.dumps({"message": "Something went wrong."}), content_type="application/json", status=500)

    def process_webhooks(self):
        # perform operation
        request_json = self.__process_request()

        pipeline_instance = self.workflow_module.start_pipeline_via_repo(request_json['repository']['clone_url'],
                                                                         self._build_request_parameters(request_json))

        if pipeline_instance:
            return Response(json.dumps(pipeline_instance), content_type="application/json")
        else:
            return Response(json.dumps({"message": "Something went wrong."}), content_type="application/json", status=500)

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
                except:
                    pass
        return parameters

    def _get_json_value(self, request_json, key):
        if '.' in key:
            tmp = key.split('.', 1)
            if tmp[0] in request_json:
                return self._get_json_value(request_json[tmp[0]], tmp[1])
            else:
                return None
        else:
            return request_json[key] if key in request_json else None

    def safe_get_value(self, json, key, value):
        return json[key][value] if key in json and value in json[key] else None
