import logging
import importlib

from rapid.lib.configuration import Configuration
from rapid.lib.framework.injectable import Injectable
logger = logging.getLogger('rapid')


class ExtensionLoader(Injectable):
    __injectables__ = {'rapid_config': None}

    def __init__(self, rapid_config):
        self.rapid_config = rapid_config

    def load_extensions(self, flask_app):
        if self.rapid_config.extensions:
            for extension in self.rapid_config.extensions:
                try:
                    extension_module = importlib.import_module(extension)
                    if hasattr(extension_module, 'setup_rapid'):
                        extension_module.setup_rapid(flask_app, self.rapid_config)
                        logger.info('The extension "{}" was loaded.'.format(extension))
                        continue
                    logger.info("The extension '{}' does not have a 'setup_rapid' method.".format(extension))
                except (ModuleNotFoundError, ImportError):
                    logger.info('The extension named "{}" was not loaded.'.format(extension))
