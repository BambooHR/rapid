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

import abc

from rapid.lib.constants import Constants


class AbstractParser(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, workspace='', failures_only=False, failures_count=False):
        self.workspace = workspace
        self.failures_only = failures_only
        self.failures_count = failures_count

    @abc.abstractmethod
    def _parse_lines(self, lines):
        yield

    @staticmethod
    @abc.abstractmethod
    def get_type():
        yield

    def prepare_summary(self):
        return {Constants.STATUS_FAILED: 0, Constants.STATUS_SUCCESS: 0, Constants.STATUS_SKIPPED: 0, Constants.FAILURES_COUNT: self.failures_count}

    def parse(self, lines, ignore_type_check=False):
        if self.get_type() != lines[0].strip() and not ignore_type_check:
            raise Exception("Invalid first line identifier")

        if ignore_type_check:
            return self._parse_lines(lines)
        
        return self._parse_lines(lines[1:])
