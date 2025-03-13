from typing import Type, TypeVar
from unittest import TestCase

from mock.mock import MagicMock

from rapid.lib import IOC
from rapid.lib.framework.injectable import Injectable
from rapid.lib.framework.injector import Injector


class UnitTest(TestCase):
    def setup_ioc(self):
        IOC.set_injector(Injector)
        IOC.set_injectable(Injectable)

    def teardown_ioc(self):
        IOC.reset_ioc()

    T = TypeVar('T')

    def fill_object_with_mocks(self, clzz: Type[T], *args, **kwargs) -> T:
        tmp_args = list(args)
        if hasattr(clzz.__init__, '__code__'):
            tmp_args.extend([MagicMock() for i in range(0, len(clzz.__init__.__code__.co_varnames) - 1 - len(args))])
        tmp_kwargs = dict(kwargs)
        if tmp_kwargs:
            for key, value in tmp_kwargs.items():
                index = -1
                for var_name in clzz.__init__.__code__.co_varnames:
                    if var_name == key:
                        tmp_args[index] = value
                    index += 1
        return clzz(*tmp_args)
