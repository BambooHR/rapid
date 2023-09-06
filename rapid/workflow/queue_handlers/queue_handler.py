from abc import ABC, abstractmethod

from rapid.master.master_configuration import MasterConfiguration


class QueueHandler(ABC):
    _GRAIN_SPLIT = '://'

    def __init__(self, rapid_config: MasterConfiguration):
        self.rapid_config = rapid_config

    @abstractmethod
    def process_work_request(self, work_request, clients):
        yield

    @abstractmethod
    def can_process_work_request(self, work_request):
        # type: (WorkRequest) -> bool
        yield

    @abstractmethod
    def process_action_instance(self, action_instance, clients):
        # type: (dict, list) -> bool
        yield

    @abstractmethod
    def can_process_action_instance(self, action_instance):
        # type: (dict) -> bool
        yield

    @abstractmethod
    def cancel_worker(self, action_instance):
        # type: (dict) -> bool
        yield

    def _get_grain_type_split(self, grain):
        return grain.split(self._GRAIN_SPLIT, 1)
