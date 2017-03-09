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

from rapid.lib.framework.IOC import IOC

registered_dals = []


def get_dal(model):
    global registered_dals
    for dal in registered_dals:
        if dal.is_serviceable(model):
            return dal
    return None


def setup_dals(flask_app):
    from rapid.master.data.database.dal.GeneralDal import GeneralDal
    from rapid.workflow.data.dal.PipelineDal import PipelineDal

    for dal in [PipelineDal, GeneralDal]:
        tmp = IOC.get_class_instance(dal)
        tmp.register_url_rules(flask_app)
        registered_dals.append(tmp)
