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
import json
import logging
import requests

from rapid.lib.constants import EventTypes
from rapid.workflow.events.event_handler import EventHandler
# pylint: disable=broad-except

logger = logging.getLogger('rapid')


class RemoteNotification(object):
    def __init__(self, config):
        self.headers = {}
        self.url = None
        self.payload = None
        self.verify = True
        
        for key in ['headers', 'url', 'payload', 'verify']:
            try:
                setattr(self, key, config[key])
            except Exception:
                pass

    def send(self):
        response = requests.post(self.url, headers=self.headers, json=self.payload, verify=self.verify, timeout=5)
        if response.status_code != 200:
            logger.error("Remote Notification Failed to send to [{}] with status: {}".format(self.url, response.status_code))
        return response


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
        if self.passes_conditional(pipeline_instance, action_instance, event.conditional):
            config_dict = {}
            try:
                config_dict = json.loads(event.config)
            except Exception:
                pass
            config = self.prepare(config_dict, pipeline_instance, action_instance)
            notification = RemoteNotification(config)
            response = notification.send()

            if response.status_code >= 400:
                logger.error("Remote Notification was not sent for: {} with status: {}".format(pipeline_instance.id, response.status_code))

    def prepare(self, config, pipeline_instance, action_instance):
        parameters = pipeline_instance.get_parameters_dict()
        config['payload'] = self.prepare_payload(config, pipeline_instance, action_instance, parameters)
        config['headers'] = self.prepare_headers(config, pipeline_instance, action_instance, parameters)
        config['url'] = self.prepare_url(config, pipeline_instance, action_instance, parameters)
        return config

    def prepare_headers(self, config, pipeline_instance, action_instance, parameters):
        headers = None
        try:
            headers = self.__replace_with_parameters(config['headers'], pipeline_instance, action_instance, parameters)
        except Exception:
            pass
        return headers

    def prepare_url(self, config, pipeline_instance, action_instance, parameters):
        new_url = None
        try:
            new_url = config['url']
            new_url = self._translate_string_for_pipeline_instance(pipeline_instance, new_url)
            new_url = self._translate_string_for_action_instance(action_instance, new_url)

            if '{' in new_url and '}' in new_url:
                for key, value in parameters.items():
                    if "{{{}}}".format(key) in new_url:
                        new_url = new_url.replace('{{{}}}'.format(key), value)
        except Exception:
            pass
        return new_url

    def prepare_payload(self, config, pipeline_instance, action_instance, parameters):
        """

        :param config:
        :type config: dict
        :type parameters: dict
        :return:
        :rtype: dict
        """
        payload = None
        try:
            payload = self.__replace_with_parameters(config['payload'], pipeline_instance, action_instance, parameters)
        except Exception:
            pass
        return payload

    def __replace_with_parameters(self, config_dict, pipeline_instance, action_instance, parameters):
        new_dict = config_dict
        try:
            for key, value in config_dict.items():
                key = self._translate_string_for_pipeline_instance(pipeline_instance, key)
                key = self._translate_string_for_action_instance(action_instance, key)

                value = self._translate_string_for_pipeline_instance(pipeline_instance, value)
                value = self._translate_string_for_action_instance(action_instance, value)

                try:
                    if value.startswith('{') and value[-1] == '}':
                        new_dict[key] = parameters[value.replace('{', '').replace('}', '')]
                    elif '{' in value and '}' in value:
                        new_dict[key] = value.replace('{', '').replace('}', '')
                except Exception:
                    pass
        except Exception:
            pass
        return new_dict
