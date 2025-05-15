import datetime
from abc import ABC, abstractmethod
from typing import Dict, List, Union

from rapid.master.master_configuration import MasterConfiguration
from rapid.lib.work_request import WorkRequest
from rapid.workflow.queue_handlers.queue_handler import QueueHandler
from rapid.workflow.action_instances_service import ActionInstanceService


class ContainerHandler(QueueHandler, ABC):

    def __init__(self, rapid_config: MasterConfiguration, action_instance_service: ActionInstanceService):
        super().__init__(rapid_config)
        self.action_instance_service = action_instance_service

    @property
    @abstractmethod
    def container_identifier(self):
        yield

    @property
    def assigned_to_prefix(self) -> str:
        return ''

    def can_process_work_request(self, work_request):
        # type: (WorkRequest) -> bool
        try:
            (grain_type, image) = self._get_grain_type_split(work_request.grain)  #pylint: disable=unused-variable
            return grain_type == self.container_identifier
        except ValueError:
            pass
        return False

    def can_process_action_instance(self, action_instance):
        # type: (dict) -> bool
        try:
            (grain_type, image) = self._get_grain_type_split(action_instance['grain'])  #pylint: disable=unused-variable
            return grain_type == self.container_identifier
        except (ValueError, KeyError):
            pass
        return False

    def _set_task_status(self, action_instance_id: int, status_id: int, assigned_to: str = '',
                         start_date: Union[datetime.datetime, None] = None,
                         end_date: Union[datetime.datetime, None] = None) -> None:
        prefix = self.assigned_to_prefix
        assigned_to = f'{prefix}{assigned_to}' if prefix and prefix not in assigned_to else assigned_to
        changes: Dict[str, Union[int, str, datetime.datetime]] = {'status_id': status_id, 'assigned_to': assigned_to}
        if start_date:
            changes['start_date'] = start_date
        if end_date:
            changes['end_date'] = end_date
        self.action_instance_service.edit_action_instance(action_instance_id, changes)

    def get_default_environment(self, work_request: WorkRequest) -> List[Dict[str, str]]:
        return [{'name': 'action_instance_id', 'value': str(work_request.action_instance_id)},
         {'name': 'workflow_instance_id', 'value': str(work_request.workflow_instance_id)},
         {'name': 'pipeline_instance_id', 'value': str(work_request.pipeline_instance_id)}]
