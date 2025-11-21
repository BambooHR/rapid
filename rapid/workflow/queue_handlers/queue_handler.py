from abc import ABC, abstractmethod
from typing import Dict, List

from rapid.master.master_configuration import MasterConfiguration


class QueueHandler(ABC):
    _GRAIN_SPLIT = '://'

    def __init__(self, rapid_config: MasterConfiguration):
        self.rapid_config = rapid_config

    @abstractmethod
    def process_work_request(self, work_request, clients):
        ...

    @abstractmethod
    def can_process_work_request(self, work_request):
        # type: (WorkRequest) -> bool
        ...

    @abstractmethod
    def verify_still_working(self, action_instances: List[Dict], clients) -> List[Dict]:
        ...

    @abstractmethod
    def can_process_action_instance(self, action_instance):
        # type: (dict) -> bool
        ...

    @abstractmethod
    def cancel_worker(self, action_instance):
        # type: (dict) -> bool
        ...

    def _get_grain_type_split(self, grain):
        return grain.split(self._GRAIN_SPLIT, 1)
