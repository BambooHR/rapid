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
from enum import Enum


class Constants(object):
    REQUIRED_FILES = "__RAPIDCI_REQUIRED__:"
    REQUIRED_WITH_DIR = "__RAPIDCI_REQUIRED_WD__:"
    RESULTS = "__RAPIDCI_RESULTS__:"
    STATUS_OVERRIDE = "__RAPIDCI_STATUSES__:"
    PARAMETERS = "__RAPIDCI_PARAMETERS__:"
    STATS = "__RAPIDCI_STATS__:"
    THRESHOLD = "__RAPIDCI_FAILURE_THRESHOLD__:"
    ANALYZE_TESTS = "__RAPID_ANALYZE_TESTS__:"
    RESULTS_SUMMARY = "__summary__"
    RESULTS_TYPE = "__results_type__"
    API_PREFIX = "/api/"

    @staticmethod
    def get_api_url(uri):
        return "{}{}".format(Constants.API_PREFIX, uri)


class ModuleConstants(object):
    QA_MODULE = "qa_module"
    WORKFLOW_MODULE = "workflow_module"
    CI_MODULE = "ci_module"


class VCSConstants(object):
    GIT = 1


class StatusConstants(object):
    NEW = 1
    READY = 2
    INPROGRESS = 3
    SUCCESS = 4
    FAILED = 5
    UNKNOWN = 7
    CANCELED = 8


class TestTypes(object):
    UNIT = 1
    INTEGRATION = 2
    SELENIUM = 3
    SMOKE = 4


class StatusTypes(object):
    SUCCESS = "success"
    FAILED = "failed"
    CANCELED = "canceled"
    WARNING = "warning"


status_type_severity_mapping = {
    StatusTypes.SUCCESS: 1,
    StatusTypes.WARNING: 2,
    StatusTypes.CANCELED: 3,
    StatusTypes.FAILED: 100
}


class EventTypes(Enum):
    RemoteNotification = 1
