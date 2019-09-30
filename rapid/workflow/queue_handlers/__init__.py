def setup_queue_handlers():
    from rapid.workflow.queue_handlers.docker_queue_handler import DockerQueueHandler
    from rapid.workflow.queue_handlers.standard_queue_handler import StandardQueueHandler
    try:
        from rapid.workflow.queue_handlers.ecs_queue_handler import ECSQueueHandler
    except ImportError:
        pass
