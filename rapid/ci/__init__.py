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
from rapid.lib.modules import CiModule
from rapid.ci.ci_controller import CIController
from rapid.ci.services.vcs_service import VcsService
from rapid.ci.vcs.github_controller import GithubController
from rapid.lib.framework.ioc import IOC


def register_ioc_globals(flask_app):  # pylint: disable=unused-argument
    vcs_service = IOC.get_class_instance(VcsService)
    IOC.register_global('ci_module', vcs_service)
    IOC.register_global(CiModule, vcs_service)


def configure_module(flask_app):
    load_model_layers()

    try:
        IOC.get_class_instance(GithubController).register_url_rules(flask_app)
        IOC.get_class_instance(CIController).register_url_rules()
    except Exception: # pylint: disable=broad-except
        import traceback
        traceback.print_exc()


def load_model_layers():
    # Used for JIT loading dependencies.
    import rapid.ci.data.models  # pylint: disable=unused-import

