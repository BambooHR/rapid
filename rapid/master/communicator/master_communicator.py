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
# pylint: disable=broad-except

import logging
from concurrent.futures import ThreadPoolExecutor
import requests
from requests.exceptions import ConnectTimeout, ConnectionError  # pylint: disable=redefined-builtin

from rapid.lib.version import Version
from rapid.lib.communicator import Communicator


logger = logging.getLogger("rapid")


class MasterCommunicator(Communicator):

    @staticmethod
    def find_available_clients(clients, grain, verify_certs=True):
        pages = None
        with ThreadPoolExecutor(max_workers=5) as executor:
            pages = executor.map(MasterCommunicator.check_availability,
                                 [(client, verify_certs) for client in MasterCommunicator.filter_clients(clients, grain)])

        return pages

    @staticmethod
    def get_clients_working_on(clients, verify_certs=True):
        pages = None
        with ThreadPoolExecutor(max_workers=5) as executor:
            pages = executor.map(MasterCommunicator.get_availability,
                                 [(client, verify_certs) for client in clients])
        return pages

    @staticmethod
    def filter_clients(clients, grain):
        tmp = []
        for client in clients:
            if client.can_handle(grain) and not hasattr(client, 'no-longer-active'):
                tmp.append(client)
        return tmp

    @staticmethod
    def check_availability(to_check):
        client, verify_certs = to_check
        try:
            response = requests.get(client.get_availability_uri(), headers=client.get_headers(), verify=verify_certs, timeout=client.time_elapse)
            if response.status_code == 200:
                return client

            if response.status_code == 423:
                client.sleep = True
                return client
        except ConnectionError:
            setattr(client, 'no-longer-active', True)
        except Exception:
            import traceback
            traceback.print_exc()
        return None

    @staticmethod
    def get_availability(to_check):
        client, verify_certs = to_check
        try:
            response = requests.get(client.get_availability_uri(), headers=client.get_headers(), verify=verify_certs, timeout=client.time_elapse)
            version = response.headers[Version.HEADER] if Version.HEADER in response.headers else 'Unknown'
            results = {"version": version, "ip_address": client.ip_address, "grains": client.grains}
            results.update(response.json())
            return results
        except Exception:
            import traceback
            traceback.print_exc()
        return None

    @staticmethod
    def is_still_working_on(action_instance_id, client, verify_certs=True):
        is_still_working = False
        try:
            response = requests.get(client.get_availability_uri(), headers=client.get_headers(), verify=verify_certs)
            try:
                if 'current_work' in response.json():
                    for instance in response.json()['current_work']:
                        if int(action_instance_id) == int(instance['action_instance_id']):
                            is_still_working = True
                            break
                else:
                    logger.info("CURRENT WORK NOT FOUND: Client:[{}] Status[{}]\nContent:{}".format(client.ip_address, response.status_code, response.content))
            except Exception:
                is_still_working = True

        except (ConnectTimeout, requests.exceptions.Timeout):
            # Not sure if there is a network issue, don't do anything
            is_still_working = True
        except ConnectionError as exception:
            # Server is up, but port is down.
            logger.error(exception)
            is_still_working = False
        except Exception as exception:
            logger.info("is_still_working failed with: {}".format(str(exception)))
            logger.exception(exception)

        return is_still_working

