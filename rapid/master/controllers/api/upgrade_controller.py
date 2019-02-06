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

from flask import Response

from rapid.lib.version import Version
from rapid.lib import api_key_required
from rapid.lib.utils import UpgradeUtil


class UpgradeController(object):

    def __init__(self, flask_app):
        self.flask_app = flask_app

    def configure_routing(self):
        self.flask_app.add_url_rule('/api/upgrade/<path:version>', 'upgrade_master', api_key_required(self.upgrade_master), methods=['POST'])

    def upgrade_master(self, version):
        worked = UpgradeUtil.upgrade_version(version, self.flask_app.rapid_config)
        return Response("It worked!" if worked else "It didn't work, version {} restored!".format(Version.get_version()), status=200 if worked else 505)
