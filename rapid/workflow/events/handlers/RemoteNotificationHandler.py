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
from lib.Constants import EventTypes
from workflow.events.event_handler import EventHandler


class RemoteNotificationHandler(EventHandler):
    @staticmethod
    def get_event_type():
        """
        :return:
        :rtype: EventTypes
        """
        return EventTypes.RemoteNotification

    def handle_event(self, pipeline_instance, action_instance, event):
        """
        :param pipeline_instance:
        :type pipeline_instance: rapid.workflow.data.models.PipelineInstance
        :param action_instance:
        :type action_instance: rapid.workflow.data.models.ActionInstance
        :param event:
        :type event: rapid.workflow.data.models.PipelineEvent
        :return:
        :rtype:
        """
        try:
            if self.passes_conditional(pipeline_instance, event.conditional):
                parameters = pipeline_instance.parameters
                conditional = event.conditional
        except:
            pass
