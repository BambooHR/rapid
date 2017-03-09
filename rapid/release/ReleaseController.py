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

from rapid.lib import api_key_required, json_response
from rapid.lib.Constants import Constants, ModuleConstants
from rapid.lib.framework.Injectable import Injectable
from rapid.release.data.ReleaseDal import ReleaseDal


class ReleaseController(Injectable):
    __injectables__ = {'release_dal': ReleaseDal}

    def __init__(self, release_dal):
        """
        :type release_dal: :class:`rapid.release.data.ReleaseDal.ReleaseDal`
        :return:
        """
        self.release_dal = release_dal

    def set_status_step(self, release_id, step_id, status):
        return self.release_dal.set_release_step(release_id, step_id, status)

    def mark_step_for_commit(self, commit_identifier, step_custom_id, status_name):
        return self.release_dal.mark_step_for_commit(commit_identifier, step_custom_id, status_name)


class ReleaseRouter(Injectable):
    __injectables__ = {'release_controller': ReleaseController}

    def __init__(self, release_controller, flask_app):
        self.flask_app = flask_app
        self.release_controller = release_controller

    def configure_urls(self):
        if self.flask_app:
            self.flask_app.add_url_rule(Constants.get_api_url("releases/<int:release_id>/step/<path:step_id>/<path:status>"), "status_step", api_key_required(self.status_step), methods=["POST"])
            self.flask_app.add_url_rule(Constants.get_api_url("releases/<path:commit_identifier>/step/<path:step_custom_id>/<path:status_name>"),
                                        "mark_step_for_commit",
                                        api_key_required(self.mark_step_for_commit),
                                        methods=['POST'])

    @json_response(message="Something did not work.")
    def status_step(self, release_id, step_id, status):
        return self.release_controller.set_status_step(release_id, step_id, status)

    @json_response()
    def mark_step_for_commit(self, commit_identifier, step_custom_id, status_name):
        return self.release_controller.mark_step_for_commit(commit_identifier, step_custom_id, status_name)
