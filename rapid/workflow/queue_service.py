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

from rapid.lib.framework.injectable import Injectable
from rapid.workflow.action_dal import ActionDal


class QueueService(Injectable):
    __injectables__ = {"action_dal": ActionDal}

    def __init__(self, action_dal):
        self.action_dal = action_dal

    def get_current_work(self):
        return self.action_dal.get_workable_work_requests()

    def get_verify_working(self, time_difference):
        return self.action_dal.get_verify_working(time_difference)
