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
from rapid.lib.constants import Constants
from rapid.client.parsers.abstract_parser import AbstractParser


class TapParser(AbstractParser):
    @staticmethod
    def get_type():
        return "Tap"

    def _parse_lines(self, lines):
        results = {}
        summary = self.prepare_summary()
        check_stacktrace = False
        current_failure = None
        stacktrace = None

        for line in lines:
            line = line.rstrip()
            if line.startswith("ok"):
                if self.failures_only:
                    continue
                split = line.split(" ", 2)
                results[split[2]] = {'status': Constants.STATUS_SUCCESS}
                summary[Constants.STATUS_SUCCESS] += 1
            elif line.startswith('not ok'):
                check_stacktrace = True
                split = line.split(' ', 4)
                current_failure = split[4]
                stacktrace = ""
            elif line.endswith('...'):
                results[current_failure] = {'status': Constants.STATUS_FAILED, 'stacktrace': stacktrace}
                stacktrace = None
                current_failure = None
                check_stacktrace = False
                summary[Constants.STATUS_FAILED] += 1
            elif check_stacktrace:
                stacktrace += "{}\n".format(line)

        results['__summary__'] = summary
        return results
