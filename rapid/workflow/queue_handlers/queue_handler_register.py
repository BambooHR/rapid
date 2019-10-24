def register_queue_handler(clazz):
    from rapid.lib.queue_handler_constants import QueueHandlerConstants
    if clazz not in QueueHandlerConstants.queue_handler_classes:
        QueueHandlerConstants.queue_handler_classes.append(clazz)
    return clazz
