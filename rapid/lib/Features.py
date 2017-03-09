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

import os


class Features(object):
    TESTING = "TESTING"
    GITHUB_ALERTS = "GITHUB_ALERTS"

    full_features = [TESTING, GITHUB_ALERTS]

    enabled_features = []

    @staticmethod
    def get_enabled_features():
        features_enabled = []
        for feature in Features.full_features:
            if Features.is_enabled(feature):
                features_enabled.append(feature)
        return features_enabled

    @staticmethod
    def is_enabled(key):
        if hasattr(Features, key):
            if key in Features.enabled_features:
                return True
            else:
                if key in os.environ:
                    return os.environ[key].lower().strip() == "true"

        return False
