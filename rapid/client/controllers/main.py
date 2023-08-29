
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
import time
import requests

try:
    import simplejson as json
except ImportError:
    import json

from rapid.lib import api_key_required
from ...lib.base_controller import BaseController


class Main(BaseController):

    def __init__(self):
        self.flask_app = None

    def register_url_rules(self, flask_app):
        flask_app.add_url_rule('/fire_registration', 'registration', api_key_required(self.fire_registration))
        self.flask_app = flask_app

    def fire_registration(self):
        request = requests.post('http://rapidci.local/client/register',
                                data=json.dumps({'grains': {'something': 'more'}}),
                                headers={'content-type': 'application/json',
                                         'X-RapidCI-Port': '8002',
                                         'X-RapidCI-Time': str(time.time() * 1000)},
                                verify=self.flask_app.rapid_config.ignore_cert_verify)
        if request.status_code == 200:
            return "Success!"

        raise BaseException("There was a problem registrating.")
