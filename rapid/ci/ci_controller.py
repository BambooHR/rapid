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

from flask.globals import request

from rapid.ci.services.vcs_service import VcsService
from rapid.lib import api_key_required, json_response
from rapid.lib.framework.injectable import Injectable


class CIController(Injectable):
    __injectables__ = {'vcs_service': VcsService, 'flask_app': None}

    def __init__(self, vcs_service, flask_app):
        """

        :type vcs_service: :class:`rapid.ci.services.vcs_service.VcsService`
        :type flask_app: :class:`flask.Flask`
        :return:
        """
        self.vcs_service = vcs_service
        self.flask_app = flask_app

    def register_url_rules(self):
        self.flask_app.add_url_rule("/api/commits/<path:commit_identifier>/version", "create_version_for_commit", api_key_required(self.create_version_for_commit), methods=["PUT"])

    @json_response()
    def create_version_for_commit(self, commit_identifier):
        return self.vcs_service.create_version_for_commit(commit_identifier, request.get_json()['version'])
