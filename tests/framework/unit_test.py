from unittest import TestCase

from rapid.lib import IOC
from rapid.lib.framework.injectable import Injectable
from rapid.lib.framework.injector import Injector


class UnitTest(TestCase):
    def setup_ioc(self):
        IOC.set_injector(Injector)
        IOC.set_injectable(Injectable)
