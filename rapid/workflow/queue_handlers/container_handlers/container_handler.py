from abc import ABCMeta, abstractproperty

from rapid.lib.work_request import WorkRequest
from rapid.workflow.queue_handlers.queue_handler import QueueHandler


class ContainerHandler(QueueHandler):
    __metaclass__ = ABCMeta

    @abstractproperty
    def container_identifier(self):
        yield

    def can_process_work_request(self, work_request):
        # type: (WorkRequest) -> bool
        try:
            (grain_type, image) = self._get_grain_type_split(work_request.grain)
            return grain_type == self.container_identifier
        except ValueError:
            pass
        return False

    def can_process_action_instance(self, action_instance):
        # type: (dict) -> bool
        try:
            (grain_type, image) = self._get_grain_type_split(action_instance['grain'])
            return grain_type == self.container_identifier
        except (ValueError, KeyError):
            pass
        return False
