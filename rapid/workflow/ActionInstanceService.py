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

from rapid.lib.framework.Injectable import Injectable
from rapid.workflow.ActionDal import ActionDal


class ActionInstanceService(Injectable):
    __injectables__ = {'action_dal': ActionDal}

    def __init__(self, action_dal):
        self.action_dal = action_dal

    def finish_action_instance(self, id, post_data):
        self.action_dal.complete_action_instance(id, post_data)

    def get_action_instance_by_id(self, id):
        return self.action_dal.get_action_instance_by_id(id)

    def edit_action_instance(self, id, changes):
        return self.action_dal.partial_edit(id, changes)

    def reset_action_instance(self, id, complete_reset=False, check_status=False):
        return self.action_dal.reset_action_instance(id, complete_reset, check_status)

    def reset_pipeline_instance(self, pipeline_instance_id):
        return self.action_dal.reset_pipeline_instance(pipeline_instance_id)

    def callback(self, id, post_data):
        return self.action_dal.callback_action_instance(id, post_data)