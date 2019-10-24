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

from .injectable import Injectable


class IOC(object):
    instance = None
    global_registers = {}

    def get_instance_of(self, clzz, *args):
        if clzz is not None:
            if issubclass(clzz, Injectable):
                real_args = []
                for param in clzz.__init__.__code__.co_varnames:
                    if param in clzz.__injectables__:
                        if param in self.global_registers:
                            real_args.append(self.global_registers[param])
                        else:
                            real_args.append(self.get_instance_of(clzz.__injectables__[param]))
                real_args.extend(args)
                return clzz(*real_args)
            return clzz(*args)

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
        IOC.get_instance().global_registers[name] = value
