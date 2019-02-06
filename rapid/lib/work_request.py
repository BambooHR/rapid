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

import re


class WorkRequest(object):
    def __init__(self, data=None):
        self._grain = None
        self.cmd = None
        self.executable = None
        self.args = None
        self.environment = {}
        self.headers = {}
        self.action_instance_id = None
        self.pipeline_instance_id = None
        self.workflow_instance_id = None
        self.slice = None

        if data:
            self.prepare_to_send(data)

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def generate_from_request(self, request):
        for (attr, value) in request.json.items():
            try:
                tmp = attr
                if tmp == 'grain':
                    tmp = '_grain'
                getattr(self, tmp)
                setattr(self, tmp, value)
            except:
                pass

    def prepare_to_send(self, data_in):
        if isinstance(data_in, dict):
            for attr in vars(self).keys():
                try:
                    tmp = attr
                    if tmp == '_grain':
                        tmp = 'grain'
                    setattr(self, attr, data_in[tmp])
                except:
                    pass
        else:
            for attr in vars(self).keys():
                try:
                    tmp = attr
                    if tmp == '_grain':
                        tmp = 'grain'
                    setattr(self, attr, getattr(data_in, tmp))
                except:
                    pass

        self.set_headers()

    def set_headers(self):
        self.headers['content-type'] = 'application/json'

    @property
    def grain(self):
        if '{' in self._grain:
            match = re.findall("\{([\w\d]*)\}", self._grain)
            if match:
                tmp = self._grain
                for param in match:
                    if param in self.environment:
                        tmp = tmp.replace('{{{}}}'.format(param), self.environment[param])
                return tmp
        return self._grain


class WorkRequestEncoder(json.JSONEncoder):
    def default(self, o):
        state = o.__dict__.copy()
        state['grain'] = state.pop('_grain', None)
        return state
