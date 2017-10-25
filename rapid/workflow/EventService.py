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
from rapid.workflow.events.EventDal import EventDal


class EventService(Injectable):
    __injectables__ = {'event_dal': EventDal}

    def __init__(self, event_dal=None):
        """
        :param event_dal:
        :type event_dal: workflow.events.EventDal.EventDal
        """
        self.event_dal = event_dal

    def trigger_possible_event(self, pipeline_instance, action_instance, session=None):
        return self.event_dal.trigger_possible_event(pipeline_instance, action_instance, session)
