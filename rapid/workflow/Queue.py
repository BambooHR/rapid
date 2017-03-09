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

import datetime
import logging
from requests.exceptions import ConnectionError, Timeout, ConnectTimeout, ReadTimeout

from rapid.lib.Constants import StatusConstants
from rapid.lib.framework.Injectable import Injectable
from rapid.master.communicator.MasterCommunicator import MasterCommunicator
from rapid.workflow.ActionInstanceService import ActionInstanceService
from rapid.workflow.QueueService import QueueService

logger = logging.getLogger("rapid")


class Queue(Injectable):
    __injectables__ = {'queue_service': QueueService, 'action_instance_service': ActionInstanceService}

    def __init__(self, queue_service, action_instance_service, flask_app):
        self.queue_service = queue_service
        self.action_instance_service = action_instance_service
        self.flask_app = flask_app

    def process_queue(self, clients):
        if clients:
            for work_request in self.queue_service.get_current_work():
                """"
                1. Find a client that can do the work based off the label
                1a. If no label, any client that takes something that is not restricted to only its type
                1b. If label, only clients that that have at least that label, or only restricted to that type
                1c. First client to respond
                2. Save who was assigned the work
                2a. Store IP and set status to INPROGRESS
                3. Send the work to the client
                3a. If the client fails, unassign the work
                """
                pages = MasterCommunicator.find_available_clients(clients.values(), work_request.grain, self.flask_app.rapid_config.verify_certs)
                for client in pages:
                    if client:
                        if hasattr(client, 'sleep') and client.sleep:
                            continue
                        try:
                            self.action_instance_service.edit_action_instance(work_request.action_instance_id, {"status_id": StatusConstants.INPROGRESS,
                                                                                                                "start_date": datetime.datetime.utcnow(),
                                                                                                                "assigned_to": "{}:{}".format(client.ip_address, client.port)})

                            response = client.send_work(work_request, self.flask_app.rapid_config.verify_certs)
                            if response.status_code == 423:
                                client.sleep = True
                            elif response.status_code == 201:
                                if 'X-Exclude-Resource'.lower() in response.headers:
                                    client.sleep = True
                            else:
                                logger.info("Client didn't respond right: {} returned {}".format(client.ip_address, response.status_code))

                            break  # Break, we sent work to the other client
                        except ConnectTimeout:
                            # Should reset, this is a problem, server not there.
                            self.action_instance_service.edit_action_instance(work_request.action_instance_id, {"status_id": StatusConstants.READY,
                                                                                                                "start_date": None,
                                                                                                                "assigned_to": None})
                        except ReadTimeout as readTimeout:
                            logger.error(readTimeout)
                            logger.error(client.get_work_uri())
                        except ConnectionError as error:
                            logger.error(error)
                            logger.error(client.get_work_uri())
                        except Exception as exception:
                            logger.error(exception)
                            logger.error(client.get_work_uri())


    def verify_still_working(self, clients):
        if clients:
            for action_instance in self.queue_service.get_verify_working(self.flask_app.rapid_config.queue_consider_late_time):
                reset_action_instance = False
                if ':' not in action_instance['assigned_to']:
                    logger.info("Action Instance {} assinged without port: {}".format(action_instance['id'], action_instance['assinged_to']))
                    reset_action_instance = True
                else:
                    ip_address, port = action_instance['assigned_to'].split(':')
                    if ip_address in clients:
                        client = clients[ip_address]
                        reset_action_instance = MasterCommunicator.is_still_working_on(action_instance['id'], client,
                                                                                       self.flask_app.rapid_config.verify_certs) == False

                if reset_action_instance:
                    if self.action_instance_service.reset_action_instance(action_instance['id'], check_status=True):
                        logger.info("Resetting Action Instance:{}".format(action_instance.id))

