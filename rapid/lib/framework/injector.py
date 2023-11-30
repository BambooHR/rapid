from abc import ABC, abstractmethod


class Injector(ABC):

    @abstractmethod
    def get_instance_of(self, clzz, *args, **kwargs):
        ...



