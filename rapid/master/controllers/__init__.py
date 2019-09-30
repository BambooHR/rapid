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


def register_controllers(app):
    from rapid.master.controllers.api.utility_controller import UtilityRouter
    utility_router = UtilityRouter(app)
    utility_router.register_url_rules()

    from rapid.master.controllers.api.upgrade_controller import UpgradeController
    UpgradeController(app).configure_routing()

    from rapid.master.controllers.api.files_controller import FilesController
    FilesController(app).configure_routing()
