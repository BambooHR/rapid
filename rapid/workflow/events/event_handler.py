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
# pylint: disable=broad-except
import re
from abc import abstractmethod, ABCMeta

import pkgutil
from simpleeval import simple_eval


class EventHandlerFactory(object):

    @staticmethod
    def get_event_handler(in_type):
        """
        :param in_type:
        :type in_type: lib.Constants.EventTypes
        :return:
        :rtype: EventHandler
        """
        import rapid.workflow.events.handlers as handlers
        for importer, modname, ispkg in pkgutil.iter_modules(handlers.__path__):  # pylint: disable=unused-variable
            try:
                name = "{}.{}".format(handlers.__name__, modname)
                module = __import__(name, fromlist=[modname])
                class_name = ''.join([x.title() for x in modname.split('_')])
                tmp = getattr(module, class_name)
                if in_type in [tmp.get_event_type().value, tmp.get_event_type()]:
                    return tmp()
            except Exception:
                pass
        return None


class EventHandler(object):
    __metaclass__ = ABCMeta

    @staticmethod
    @abstractmethod
    def get_event_type():
        yield

    @abstractmethod
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
        yield

    def passes_conditional(self, pipeline_instance, action_instance, conditional):
        """
        :param pipeline_instance:
        :type pipeline_instance: workflow.data.models.PipelineInstance
        :param conditional:
        :type conditional: str
        :return:
        :rtype:
        """
        if conditional is None or conditional == '':
            return True

        new_conditional = self._prepare_conditional(conditional, pipeline_instance, action_instance)
        return self._evaluate_condition(new_conditional)

    def _prepare_conditional(self, conditional, pipeline_instance, action_instance):
        """
        :param conditional:
        :type conditional: str
        :param parameters:
        :type parameters: dict
        :return:
        :rtype:
        """
        new_conditional = conditional
        for parameter, value in pipeline_instance.get_parameters_dict().items():
            if "{{{}}}".format(parameter) in new_conditional:
                new_conditional = new_conditional.replace("{{{}}}".format(parameter), str(value))

        if 'pipelineInstance.' in new_conditional:
            new_conditional = self._translate_string_for_pipeline_instance(pipeline_instance, new_conditional)

        if 'actionInstance.' in new_conditional:
            new_conditional = self._translate_string_for_action_instance(action_instance, new_conditional)

        return new_conditional

    def _evaluate_condition(self, condition):
        try:
            return simple_eval(condition)
        except Exception:
            return False

    def _translate_string_for_pipeline_instance(self, pipeline_instance, string):
        return self._translate_string_for_key_string('pipelineInstance', pipeline_instance, string)

    def _translate_string_for_action_instance(self, action_instance, string):
        return self._translate_string_for_key_string('actionInstance', action_instance, string)

    def _translate_string_for_key_string(self, key_string, obj_instance, string):
        new_string = string
        try:
            for term in re.findall(r'(' + key_string + r'\.[^\s^}]{0,})', new_string):
                replaced_term = term.replace('{}.'.format(key_string), '', 1)
                new_string = new_string.replace(term, str(self._get_attribute_trait(obj_instance, replaced_term)))
        except Exception:
            pass
        return new_string

    def _get_attribute_trait(self, obj, trait):
        if '.' in trait:
            sp_obj = trait.split('.', 2)
            new_obj = getattr(obj, sp_obj[0])

            if len(sp_obj) > 1:
                return self._get_attribute_trait(new_obj, sp_obj[1])
            return new_obj

        return getattr(obj, trait)
