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

import socket
from abc import ABCMeta, abstractmethod
import os
try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:
    from configparser import ConfigParser

import logging

logger = logging.getLogger("rapid")


class ConfigurationDefaults(object):
    def __init__(self, default=None, type_cast=str, delim=','):
        self._default = default
        self._type_cast = type_cast
        self._delim = delim

    @property
    def defaults(self):
        return [self._default, self._type_cast, self._delim]


class Configuration(object):
    __metaclass__ = ABCMeta

    def __init__(self, file_name=None):
        self.hostname = socket.gethostname()
        self.parse_config_file(file_name)

    def parse_config_file(self, file_name):
        parser = ConfigParser()
        try:
            if file_name:
                if os.path.exists(file_name):
                    parser.read(file_name)
        except Exception:  # pylint: disable=bare-except
            logger.info("Using defaults")

        self._set_values(parser)
        return self

    @property
    @abstractmethod
    def section_mapping(self):
        """
        Returns
        -------
        dict
            dict of key, dict of key value mappings.
        """
        yield

    def get_section(self, key):
        for section, value in self.section_mapping.items():
            if key in value:
                return section
        return None

    def _set_values(self, parser):
        for section, map in self.section_mapping.items():
            for key, value in map.items():
                try:
                    self._set_parser_value(parser, section, key, *value.defaults)
                except AttributeError:
                    self._set_parser_value(parser, section, key, *value)

    def _handle_normal_value(self, parser, key, section, type_cast):
        setattr(self, key, type_cast(parser.get(section, key)))

    def _set_parser_value(self, parser, section, key, default=None, type_cast=str, delim=','):
        try:
            if type_cast == bool:
                setattr(self, key, parser.get(section, key).lower().strip() == 'true')
            elif type_cast == list:
                setattr(self, key, parser.get(section, key).split(delim))
            else:
                self._handle_normal_value(parser, key, section, type_cast)
        except Exception:  # pylint: disable=broad-except
            setattr(self, key, default)
