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

from xml.dom.minidom import parseString
from rapid.lib.constants import Constants

from .abstract_parser import AbstractParser


class XUnitParser(AbstractParser):
    @staticmethod
    def get_type():
        return "XUnit"

    def _parse_lines(self, lines):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        """
        Removes the first line, being the identifier, then parses the rest of the lines
        :param lines: array of the lines of the file.
        :return: dict of results.
        """
        results = {}
        dom = parseString("".join(lines))
        summary = self.prepare_summary()

        for testsuite in dom.getElementsByTagName('testsuite'):
            for node in testsuite.childNodes:
                if node.nodeName != 'testcase':
                    continue
                testcase = node
                name = ''
                try:
                    class_name = ''
                    for class_attr in ['classname', 'class']:
                        class_name = testcase.getAttribute(class_attr)
                        if class_name:
                            break

                    name = "{}~{}".format(class_name, testcase.getAttribute('name'))
                except AttributeError:
                    import traceback
                    traceback.print_exc()

                if self.workspace:
                    name = name.replace(self.workspace, '')

                test_result = {
                    'status': Constants.STATUS_SUCCESS,
                    'time': testcase.getAttribute('time')
                }

                failure_tags = testcase.getElementsByTagName('failure')
                skipped_tags = testcase.getElementsByTagName('skipped')
                error_tags = testcase.getElementsByTagName('error')

                if self.failures_only and (not failure_tags and not error_tags):
                    continue

                if failure_tags:
                    test_result['status'] = Constants.STATUS_FAILED
                    test_result['stacktrace'] = ""

                    count = 0
                    length = len(failure_tags)
                    for failure in failure_tags:
                        test_result['stacktrace'] += "\n".join(
                            [failure.firstChild.nodeValue if failure.firstChild is not None and hasattr(failure.firstChild, 'nodeValue')
                             else failure.attributes['message'].value])
                        count += 1
                        if length > count:
                            test_result['stacktrace'] += "\n"

                    summary[Constants.STATUS_FAILED] += 1
                elif error_tags:
                    test_result['status'] = Constants.STATUS_FAILED
                    test_result['stacktrace'] = ""

                    count = 0
                    length = len(failure_tags)
                    for failure in error_tags:
                        test_result['stacktrace'] += "\n".join(
                            ["Error - " + (failure.firstChild.nodeValue if failure.firstChild is not None and hasattr(failure.firstChild, 'nodeValue')
                                           else failure.attributes['message'].value)])
                        count += 1
                        if length > count:
                            test_result['stacktrace'] += "\n"

                    summary[Constants.STATUS_FAILED] += 1
                elif skipped_tags:
                    test_result['status'] = Constants.STATUS_SKIPPED
                    summary[Constants.STATUS_SKIPPED] += 1
                else:
                    summary[Constants.STATUS_SUCCESS] += 1

                results[name] = test_result

        results['__summary__'] = summary

        return results
