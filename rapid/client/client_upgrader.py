import logging

from flask import Flask

from rapid.client import ClientCommunicator
from rapid.client.client_configuration import ClientConfiguration
from rapid.lib.utils import UpgradeUtil
from rapid.lib.version import Version

logger = logging.getLogger('rapid')


class ClientUpgrader(object):
    def __init__(self, rapid_config):
        # type: (ClientConfiguration) -> None
        self.client_config = rapid_config

    def upgrade(self, app):
        # type: (Flask) -> None
        communicator = ClientCommunicator(self.client_config.master_uri, self.client_config.quarantine_directory, app, self.client_config.verify_certs)
        self.client_config.is_single_use = True

        info = communicator.register(self.client_config)
        if info['master_version'] != Version.get_version():
            logger.info("Found Version: {}".format(info['master_version']))
            # UpgradeUtil.upgrade_version(info['master_version'], self.client_config)
            UpgradeUtil.upgrade_version(info['master_version'], self.client_config)
        else:
            logger.info("Versions match. No need to upgrade")
