def register_queue_handler(clazz):
    if clazz not in QueueHandlerConstants.queue_handler_classes:
        QueueHandlerConstants.queue_handler_classes.append(clazz)
    return clazz


class QueueHandlerConstants(object):
    queue_handler_classes = []
