

class QueueHandlerConstants:
    queue_handler_classes = []

    def __init__(self):
        self._queue_handlers = None

    @property
    def queue_handlers(self):
        if self._queue_handlers is None:
            self.load_handlers()
        return self._queue_handlers

    def load_handlers(self):
        from rapid.lib import IOC
        for handler_class in self.queue_handler_classes:
            self.queue_handlers.append(IOC.get_class_instance(handler_class))

    def cancel_worker(self, action_instance):  # type: (dict) -> bool
        for handler in self.queue_handlers:
            if handler.can_process_action_instance(action_instance):
                return handler.cancel_worker(action_instance)
        return False
