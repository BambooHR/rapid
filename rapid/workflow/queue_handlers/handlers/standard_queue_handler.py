import logging
import datetime
import random

from requests import ConnectTimeout, ReadTimeout, ConnectionError

from rapid.lib.constants import StatusConstants
from rapid.lib.framework.injectable import Injectable
from rapid.lib.store_service import StoreService
from rapid.master.communicator.master_communicator import MasterCommunicator
from rapid.workflow.action_instances_service import ActionInstanceService
from rapid.workflow.queue_handlers.queue_handler import QueueHandler
from rapid.workflow.queue_handlers.queue_handler_register import register_queue_handler

logger = logging.getLogger('rapid')


@register_queue_handler
class StandardQueueHandler(QueueHandler, Injectable):
    __injectables__ = {'rapid_config': None,
                       'action_instance_service': ActionInstanceService,
                       'flask_app': None}

    def process_work_request(self, work_request, clients):
        """
        1. Find a client that can do the work based off the label
          1a. If no label, any client that takes something that is not restricted to only its type
          1b. If label, only clients that that have at least that label, or only restricted to that type
          1c. First client to respond
        2. Save who was assigned the work
          2a. Store IP and set status to INPROGRESS
        3. Send the work to the client
          3a. If the client fails, unassign the work
        """
        clients_array = clients.values()
        random.shuffle(clients_array)
        pages = MasterCommunicator.find_available_clients(clients_array, work_request.grain, self.rapid_config.verify_certs)
        for client in pages:
            if client:
                if hasattr(client, 'sleep') and client.sleep:
                    continue
                try:
                    self.action_instance_service.edit_action_instance(work_request.action_instance_id, {"status_id": StatusConstants.INPROGRESS,
                                                                                                        "start_date": datetime.datetime.utcnow(),
                                                                                                        "assigned_to": "{}:{}".format(client.ip_address, client.port)})
                    try:
                        response = client.send_work(work_request, self.rapid_config.verify_certs)
                        if response.status_code == 423:
                            client.sleep = True
                            raise Exception("Client was busy, can't take work.")
                        if response.status_code == 201:
                            if 'X-Exclude-Resource'.lower() in response.headers:
                                client.sleep = True
                        else:
                            logger.info("Client didn't respond right: {} returned {}".format(client.ip_address, response.status_code))

                        break  # Break, we sent work to the other client
                    except Exception as exception:
                        logger.error("Could not send work to worker: [{}]".format(str(exception)))
                        self.action_instance_service.edit_action_instance(work_request.action_instance_id, {"status_id": StatusConstants.READY,
                                                                                                            "start_date": None,
                                                                                                            "assigned_to": None})
                except ConnectTimeout:
                    # Should reset, this is a problem, server not there.
                    self.action_instance_service.edit_action_instance(work_request.action_instance_id, {"status_id": StatusConstants.READY,
                                                                                                        "start_date": None,
                                                                                                        "assigned_to": None})
                except ReadTimeout as read_timeout:
                    logger.error(read_timeout)
                    logger.error(client.get_work_uri())
                except ConnectionError as error:
                    logger.error(error)
                    logger.error(client.get_work_uri())
                except Exception as exception:
                    logger.error(exception)
                    logger.error(client.get_work_uri())
        pages = None
        clients_array = None

    def __init__(self, rapid_config, action_instance_service, flask_app):
        """
        :param rapid_config:
        :type rapid_config: rapid.master.master_configuration.MasterConfiguration
        :param action_instance_service:
        :type action_instance_service: rapid.workflow.action_instance_service.ActionInstanceService
        :type flask_app: Flask
        """
        super(StandardQueueHandler, self).__init__(rapid_config)
        self.action_instance_service = action_instance_service
        self.flask_app = flask_app

    def can_process_work_request(self, work_request):
        return len(self._get_grain_type_split(work_request.grain)) < 2

    def can_process_action_instance(self, action_instance):
        return len(self._get_grain_type_split(action_instance['grain'])) < 2

    def process_action_instance(self, action_instance, clients):  # type: (dict, list) -> bool
        reset_action_instance = False
        if ':' not in action_instance['assigned_to']:
            logger.info("Action Instance {} assigned without port: {}".format(action_instance['id'], action_instance['assigned_to']))
            reset_action_instance = True
        else:
            ip_address, port = action_instance['assigned_to'].split(':')  # pylint: disable=unused-variable
            if ip_address in clients:
                client = clients[ip_address]
                reset_action_instance = MasterCommunicator.is_still_working_on(action_instance['id'], client,
                                                                               self.rapid_config.verify_certs) is False

        if reset_action_instance and not StoreService.is_completing(action_instance['id']):
            if self.action_instance_service.reset_action_instance(action_instance['id'], check_status=True):
                logger.info("Resetting Action Instance:{} was assigned to: {}".format(action_instance['id'], action_instance['assigned_to']))
        return True

    def cancel_worker(self, action_instance):  # type: (dict) -> bool
        for client in StoreService.get_clients(self.flask_app).values():
            if client.get_uri() == action_instance['assigned_to']:
                client.cancel_work(action_instance['id'], self.flask_app.rapid_config.verify_certs)
                break
        return True
