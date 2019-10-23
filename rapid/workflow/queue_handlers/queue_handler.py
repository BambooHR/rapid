from abc import ABCMeta, abstractmethod


class QueueHandler(object):
    _GRAIN_SPLIT = '://'
    __metaclass__ = ABCMeta

    def __init__(self, rapid_config):
        """
        Parameters
        ----------
        rapid_config: rapid.master.master_configuration.MasterConfiguration
        """
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
