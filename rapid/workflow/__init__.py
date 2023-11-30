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
from rapid.lib.framework.ioc import IOC


def register_ioc_globals(flask_app):  # pylint: disable=unused-argument
    from rapid.workflow.action_service import ActionService
    from rapid.workflow.workflow_service import WorkflowService
    from rapid.lib.queue_handler_constants import QueueHandlerConstants
    from rapid.workflow.queue_handlers import setup_queue_handlers

    setup_queue_handlers()
    constants = IOC.get_class_instance(QueueHandlerConstants)

    workflow_service = IOC.get_class_instance(WorkflowService)
    action_service = IOC.get_class_instance(ActionService)

    # IOC.register_global(QueueHandlerConstants, constants)
    # IOC.register_global(WorkflowService, workflow_service)
    # IOC.register_global(ActionService, action_service)
    IOC.register_global('queue_constants', constants)
    IOC.register_global('workflow_module', workflow_service)
    IOC.register_global('action_module', action_service)


def configure_module(flask_app):
    from rapid.workflow.api_controller import APIRouter
    router = IOC.get_class_instance(APIRouter)
    router.register_url_rules(flask_app)


