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
from typing import Type, Any, TypeVar

from .injectable import Injectable
from ..constants import FrameworkConstants

T = TypeVar('T')  # pylint: disable=invalid-name
OB = TypeVar('OB', bound=object)


class IOC:
    """
    IOC Injection module
    """
    _instance = None
    _overrides = {}
    _injectable = None
    _no_cacheable: Type[OB] = None
    _injector = None

    def __init__(self):
        self._cache = {}
        self.is_cached = False

    @classmethod
    def override(cls, key: str or Type[Any], value: object) -> None:
        cls._overrides[key] = value

    @classmethod
    def is_injectable(cls, clzz: Type[T]) -> bool:
        if cls._injectable:
            return issubclass(clzz, cls._injectable)
        return False

    def _cache_value(self, key: Type[T], value: OB):
        if self._cache is not None and self.is_cached:
            if self._no_cacheable is not None and not isinstance(value, self._no_cacheable):  # pylint: disable=isinstance-second-argument-not-valid-type
                self._cache[key] = value

    def get_instance_of(self, clzz: Type[T], *args, **kwargs) -> T:
        try:
            if self.is_cached and clzz in self._cache:
                return self._cache[clzz]

            if clzz in IOC._overrides:
                return IOC._overrides[clzz]

            if hasattr(clzz, '__origin__'):
                ioc_args = clzz.__args__
                clzz = clzz.__origin__
                setattr(clzz, '__ioc_args__', ioc_args)

            is_injectable = self.is_injectable(clzz)
            if is_injectable:
                real_args = []
                real_args.extend(args[:1])
                real_args.extend(self._get_dynamic_args(clzz, kwargs))
                real_args.reverse()
                real_args.extend(args[1:])
                clzz_instance = clzz(*real_args)

                if not args and not kwargs:
                    self._cache_value(clzz, clzz_instance)

                return clzz_instance
            clzz_instance = clzz(*args, **kwargs)
            if is_injectable and (not args and not kwargs):
                self._cache_value(clzz, clzz_instance)
            return clzz_instance
        except TypeError:
            pass
        return None

    def _get_dynamic_args(self, clzz, kwargs: dict):
        dynamic_args = []
        _signature = inspect.signature(clzz.__init__).parameters
        _full_argspec = inspect.getfullargspec(clzz.__init__)
        arg_spec = _full_argspec.annotations

        if clzz.__init__ and hasattr(clzz.__init__, '__code__'):
            for param in clzz.__init__.__code__.co_varnames:
                if param == 'self':
                    continue
                if param in IOC._overrides:
                    dynamic_args.append(IOC._overrides[param])
                elif param in kwargs.keys():
                    dynamic_args.append(kwargs[param])
                elif param in arg_spec:
                    arg = arg_spec[param]
                    if arg in IOC._overrides:
                        if inspect.isclass(IOC._overrides[arg]):
                            dynamic_args.append(self.get_instance_of(IOC._overrides[arg]))
                        else:
                            dynamic_args.append(IOC._overrides[arg])
                    elif self.is_cached and arg in self._cache:
                        dynamic_args.append(self._cache[arg])
                    elif self._injector is not None and arg == self._injector:
                        dynamic_args.append(self)
                    elif self.is_injectable(arg) and not FrameworkConstants.is_primitive(arg):
                        arg_instance = self.get_instance_of(arg)

                        self._cache_value(arg, arg_instance)

                        dynamic_args.append(arg_instance)
                    elif issubclass(arg, object) \
                            and not FrameworkConstants.is_primitive(arg) \
                            and not FrameworkConstants.is_structure(arg) \
                            and (not hasattr(arg.__init__, '__code__') or len(arg.__init__.__code__.co_varnames) == 1):
                        arg_instance = arg()

                        self._cache_value(arg, arg_instance)

                        dynamic_args.append(arg_instance)
                    elif param in _signature and _signature[param].default is not inspect.Parameter.empty:
                        dynamic_args.append(_signature[param].default)

            dynamic_args.reverse()
        return dynamic_args

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = IOC()
        return cls._instance

    @classmethod
    def reset_ioc(cls):
        cls._instance = None
        cls._overrides = {}
        cls._injectable = None
        cls._no_cacheable: Type[OB] = None
        cls._injector = None

    @classmethod
    def get_class_instance(cls, clzz: Type[T], *args, **kwargs) -> T:
        return cls.get_instance().get_instance_of(clzz, *args, **kwargs)

    @classmethod
    def register_global(cls, name: Any, value: Any):
        cls.override(name, value)

    @classmethod
    def set_injectable(cls, injectable: Type[OB]):
        cls._injectable = injectable

    @classmethod
    def set_injector(cls, injector: Type[OB]):
        cls._injector = injector

    @classmethod
    def set_no_cacheable(cls, no_cacheable: Type[OB]):
        cls._no_cacheable = no_cacheable

