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
import logging

from rapid.lib.constants import EventTypes
from rapid.lib.framework.injectable import Injectable
from rapid.master.data.database.dal.general_dal import GeneralDal
from rapid.workflow.data.dal.pipeline_dal import PipelineDal
from rapid.workflow.events.event_handler import EventHandlerFactory


class EventDal(GeneralDal, Injectable):
    __injectables__ = {'pipeline_dal': PipelineDal}

    def __init__(self, pipeline_dal):
        """
        :param pipeline_dal:
        :type pipeline_dal: PipelineDal
        """
        self.pipeline_dal = pipeline_dal

    def trigger_possible_event(self, pipeline_instance, action_instance, session=None):
        """
        :param pipeline_instance:
        :type pipeline_instance: rapid.workflow.data.models.PipelineInstance
        :param action_instance:
        :type action_instance: rapid.workflow.data.models.ActionInstance
        :param session:
        :type session:
        :return:
        :rtype:
        """
        for event in self.pipeline_dal.get_pipeline_events_by_pipeline_id(pipeline_instance.pipeline_id, session=session):
            try:
                handler = EventHandlerFactory.get_event_handler(EventTypes(event.event_type_id))
                handler.handle_event(pipeline_instance, action_instance, event)
            except Exception:  # pylint: disable=broad-except
                pass
