import importlib
import pkgutil


def setup_queue_handlers():
    internal_module = _get_internal_module()
    for info in pkgutil.iter_modules(internal_module.__path__):
        module_name = None
        try:
            module_name = info.name
        except AttributeError:
            module_name = info[1]
        try:
            importlib.import_module('.'.join([internal_module.__name__, module_name]))
        except ImportError:
            pass


def _get_internal_module():
    return importlib.import_module('{}.handlers'.format(__name__))
