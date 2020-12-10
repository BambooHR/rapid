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
import inspect
from typing import Type, Any

from rapid.lib.framework.injectable import Injectable
from rapid.lib.constants import Constants


class IOC:
    instance = None
    global_registers = {}
    overrides = {}

    def override(self, key: str or Type[Any], value: object):
        self.overrides[key] = value

    def _get_dynamic_args(self, clzz):
        dynamic_args = []
        arg_spec = inspect.getfullargspec(clzz.__init__).annotations
        if clzz.__init__ and hasattr(clzz.__init__, '__code__'):
            for param in clzz.__init__.__code__.co_varnames:
                if param == 'self':
                    continue
                if param in self.overrides:
                    dynamic_args.append(self.overrides[param])
                elif param in arg_spec:
                    arg = arg_spec[param]
                    if arg in self.overrides:
                        if inspect.isclass(self.overrides[arg]):
                            dynamic_args.append(self.get_instance_of(self.overrides[arg]))
                        else:
                            dynamic_args.append(self.overrides[arg])
                    elif issubclass(arg, Injectable) and not Constants.is_primitive(arg):
                        dynamic_args.append(self.get_instance_of(arg))
                    elif issubclass(arg, object) \
                            and not Constants.is_primitive(arg) \
                            and not Constants.is_structure(arg) \
                            and (not hasattr(arg.__init__, '__code__') or len(arg.__init__.__code__.co_varnames) == 1):
                        dynamic_args.append(arg())
            dynamic_args.reverse()
        return dynamic_args

    def get_instance_of(self, clzz, *args):
        try:
            if issubclass(clzz, Injectable):
                real_args = []
                real_args.extend(args[:1])
                real_args.extend(self._get_dynamic_args(clzz))
                real_args.reverse()
                real_args.extend(args[1:])
                return clzz(*real_args)
            return clzz(*args)
        except TypeError:
            pass
        return None

    @staticmethod
    def get_instance():
        if IOC.instance is None:
            IOC.instance = IOC()
        return IOC.instance

    @staticmethod
    def get_class_instance(clzz, *args):
        return IOC.get_instance().get_instance_of(clzz, *args)

    @staticmethod
    def register_global(name, value):
        IOC.get_instance().overrides[name] = value
