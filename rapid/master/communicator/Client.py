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

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from rapid.lib.Version import Version
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class Client(object):

    def __init__(self, ip_address, port, grains, grain_restrict, api_key=None, is_ssl=False, hostname=None):
        self.ip_address = ip_address
        self.is_ssl = is_ssl
        self.port = port
        self.grains = grains.split(';') if grains is not None else None
        self.grain_restrict = grain_restrict
        self.sleep = False
        self.api_key = api_key
        self.hostname = hostname

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def get_headers(self):
        return {'X-Rapidci-Version': Version.get_version(), 'Content-Type': 'application/json', 'X-Rapidci-Api-Key': self.api_key}

    def can_handle(self, grain):
        if self.sleep:
            return False
        elif grain is not None and self.grains is not None:
            tmp_grains = grain.split(';')
            number_matched = 0
            for gr in tmp_grains:
                if gr not in self.grains:
                    return False
                number_matched += 1

            if self.grain_restrict and number_matched != len(self.grains):
                return False

            return True
        elif self.grain_restrict:
            return False
        return True

    def get_availability_uri(self):
        return "{}://{}:{}/work/request".format(self._get_prefix(), self.ip_address, self.port)

    def get_work_uri(self):
        return "{}://{}:{}/work/execute".format(self._get_prefix(), self.ip_address, self.port)

    def get_status_uri(self):
        return "{}://{}:{}/status".format(self._get_prefix(), self.ip_address, self.port)

    def send_work(self, work_request, verify_certs=True):
        return requests.post(self.get_work_uri(), json=json.dumps(work_request.__dict__), headers=self.get_headers(), verify=verify_certs, timeout=4)

    def _get_prefix(self):
        return 'https' if self.is_ssl else 'http'