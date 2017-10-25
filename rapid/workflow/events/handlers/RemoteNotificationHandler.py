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

import json
import requests

from rapid.lib.Constants import EventTypes
from rapid.workflow.events.event_handler import EventHandler

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
            except:
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
            except:
                pass
            config = self.prepare(config_dict, pipeline_instance._get_parameters_dict())
            notification = RemoteNotification(config)
            response = notification.send()

            if response.status_code >= 400:
                logger.error("Remote Notification was not sent for: {} with status: {}".format(pipeline_instance.id, response.status_code))

    def prepare(self, config, parameters):
        config['payload'] = self.prepare_payload(config, parameters)
        config['headers'] = self.prepare_headers(config, parameters)
        config['url'] = self.prepare_url(config, parameters)
        return config

    def prepare_headers(self, config, parameters):
        headers = None
        try:
            headers = self.__replace_with_parameters(config['headers'], parameters)
        except:
            pass
        return headers

    def prepare_url(self, config, parameters):
        new_url = None
        try:
            new_url = config['url']
            if '{' in new_url and '}' in new_url:
                for key, value in parameters.items():
                    if "{{{}}}".format(key) in new_url:
                        new_url = new_url.replace('{{{}}}'.format(key), value)
        except:
            pass
        return new_url

    def prepare_payload(self, config, parameters):
        """

        :param config:
        :type config: dict
        :type parameters: dict
        :return:
        :rtype: dict
        """
        payload = None
        try:
            payload = self.__replace_with_parameters(config['payload'], parameters)
        except:
            pass
        return payload

    def __replace_with_parameters(self, config_dict, parameters):
        new_dict = config_dict
        try:
            for key, value in config_dict.items():
                try:
                    if value.startswith('{') and value[-1] == '}':
                        new_dict[key] = parameters[value.replace('{', '').replace('}', '')]
                except:
                    pass
        except:
            pass
        return new_dict