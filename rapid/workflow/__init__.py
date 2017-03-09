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

from rapid.lib.framework.IOC import IOC


def register_ioc_globals(flask_app):
    from rapid.workflow.ActionService import ActionService
    from rapid.workflow.WorkflowService import WorkflowService

    IOC.register_global('workflow_module', IOC.get_class_instance(WorkflowService))
    IOC.register_global('action_module', IOC.get_class_instance(ActionService))


def configure_module(flask_app):
    from rapid.workflow.APIController import APIRouter
    router = IOC.get_class_instance(APIRouter)
    router.register_url_rules(flask_app)


