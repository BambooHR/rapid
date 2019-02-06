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
from rapid.qa.qa_service import QaService


def register_ioc_globals(flask_app):  # pylint: disable=unused-argument
    IOC.register_global('qa_module', IOC.get_class_instance(QaService))


def configure_module(flask_app):
    from rapid.qa.controllers.qa_controller import QAController
    controller = IOC.get_class_instance(QAController)
    controller.register_url_rules(flask_app)

    load_model_layers()


def load_model_layers():
    import rapid.qa.data.models  # pylint: disable=unused-import

