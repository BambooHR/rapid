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
# pylint: disable=broad-except
import logging
from abc import ABCMeta, abstractmethod
import os

import re

from rapid.lib.utils import deep_merge

logger = logging.getLogger("rapid")


class QaTestFile(object):
    __metaclass__ = ABCMeta

    AREA = "area"
    FEATURE = "feature"
    BP = "behavior_point"

    def __init__(self, filename, rootdir):
        self._tests = []
        self._filename = filename
        self._current_settings = {}
        self._found_tests = False
        self._areas = {}
        self._current_test = {}
        self._rootdir = rootdir

    @abstractmethod
    def is_reversed(self):
        raise Exception("Should implement this.")

    @property
    @abstractmethod
    def regex(self):
        raise Exception("Should implement regex.")

    def get_results(self):
        return self._areas

    def parse_file(self, name_map=None):
        with open(self._filename) as file:
            for line in file.readlines():
                try:
                    action = self.parse_action(line)
                    if action:
                        try:
                            getattr(self, "handle_{}".format(action))(line)
                        except Exception:
                            pass
                    else:
                        self.handle_test(line, name_map)
                except Exception:
                    import traceback
                    traceback.print_exc()

        if self.is_reversed() and self._current_settings:
            self._finalize_test(self._current_test)

    def parse_action(self, line):
        tmp = self._strip_comment_characters(line).lstrip()
        if tmp.startswith('rapid-') or tmp.startswith('@rapid-'):
            _match = re.findall('rapid-([a-zA-Z]+)', tmp)
            if _match and len(_match) >= 1:
                return _match[0]
        return None

    def handle_unit(self, line):
        self._current_settings['level'] = 'unit'
        self.parse_test_levels(re.split('rapid-unit:?', line)[1].strip())

    def handle_integration(self, line):
        self._current_settings['level'] = 'integration'
        self.parse_test_levels(re.split('rapid-integration:?', line)[1].strip())

    def handle_selenium(self, line):
        self._current_settings['level'] = 'selenium'
        self.parse_test_levels(re.split('rapid-selenium:?', line)[1].strip())

    def handle_tags(self, line):
        self._current_settings['tags'] = re.split('rapid-tags:?', line)[1].strip().split()

    def parse_test_levels(self, string):
        """
        :param string: 
        :type string: str 
        :return: 
        :rtype: 
        """
        split_char = ':'
        if '|' in string:
            split_char = '|'
        (area, feature, behavior_point) = string.split(split_char, 2)
        self._current_settings[self.AREA] = area
        self._current_settings[self.FEATURE] = feature
        self._current_settings[self.BP] = behavior_point

    def _strip_comment_characters(self, line):
        tmp = line.lstrip().rstrip("\n")
        return tmp.lstrip(self._get_comment_characters())

    @abstractmethod
    def _get_comment_characters(self):
        yield

    def _get_behavior_point_map(self, area, feature, behavior_point):
        area_map = self.__check_area(area)
        feature_map = self.__check_feature(area_map, feature)
        return self.__check_behavior_points(feature_map, behavior_point)

    def __check_area(self, area):
        if not self._areas.get(area, None):
            self._areas[area] = {}
        return self._areas[area]

    def __check_feature(self, area_map, feature):
        if not area_map.get(feature, None):
            area_map[feature] = {}
        return area_map.get(feature)

    def __check_behavior_points(self, feature_map, behavior_point):
        if not feature_map.get(behavior_point, None):
            feature_map[behavior_point] = []
        return feature_map[behavior_point]

    def handle_test(self, line, name_map=None):
        if self.regex:
            groups = re.findall(self.regex, line)
            if groups:
                name = groups[0]
                if name_map is not None and name in name_map:
                    name = name_map[name]

                test = {"name": name, "current_settings": dict(self._current_settings) if not self.is_reversed() else {}}
                self._tests.append(test)
                if self.is_reversed():
                    if self._current_test:
                        self._finalize_test(self._current_test)

                    self._current_test = test
                    self._current_settings = test['current_settings']
                else:
                    self._finalize_test(test)
                    self._current_settings = {}
                self._found_tests = True

    def _finalize_test(self, test):
        if test['current_settings'].get('area', None):
            _bp = self._get_behavior_point_map(test['current_settings'].get(self.AREA, None),
                                               test['current_settings'].get(self.FEATURE, None),
                                               test['current_settings'].get(self.BP, None))

            _bp.append(test)

    def printout(self):
        if self._areas:
            for area, area_map in list(self._areas.items()):
                for feature, feature_map in list(area_map.items()):
                    for _bp, tests in list(feature_map.items()):
                        print("{}:{}:{}".format(area, feature, _bp))
                        for test in tests:
                            print("      - ({}) {} -- [{}]".format(test['current_settings'].get('level'), test['name'],
                                                                   ",".join(test['current_settings'].get('tags', []))))


class PythonFile(QaTestFile):
    def _get_comment_characters(self):
        return "#"

    _CUSTOM_RE = re.compile(r'\s{1,}def (test[\S]*)\(.*$')

    @property
    def regex(self):
        return self._CUSTOM_RE

    def is_reversed(self):
        return True


class PHPFile(QaTestFile):
    def _get_comment_characters(self):
        return "/*"

    _CUSTOM_RE = re.compile(r'\s{1,}function (test[\S]*)\(.*$')

    @property
    def regex(self):
        return self._CUSTOM_RE

    def is_reversed(self):
        return False


class JSFile(QaTestFile):
    def _get_comment_characters(self):
        return "/*"

    _CUSTOM_RE = re.compile(r'\s{1,}it\([\'"`]([^\'`"]*)')

    @property
    def regex(self):
        return self._CUSTOM_RE

    def is_reversed(self):
        return False


class FileTestFactory(object):
    @staticmethod
    def create_file_test(filename, rootdir):
        """
        :return FileTest
        """
        file_type = filename.split('.')[-1]
        if file_type == 'php':
            return PHPFile(filename, rootdir)
        if file_type == 'py':
            return PythonFile(filename, rootdir)
        if file_type == 'js':
            return JSFile(filename, rootdir)
        return None


def process_directory(workspace, dirname, cmdline=False, name_map=None):
    results = {}
    for root, dirs, files in os.walk(dirname):  # pylint: disable=unused-variable
        for filename in files:
            try:
                testfile = FileTestFactory.create_file_test("{}/{}".format(root, filename), workspace)
                if testfile:
                    testfile.parse_file(name_map)
                    deep_merge(results, testfile.get_results())
            except Exception as exception:
                logger.error("Was Unable to process the directory defined. {}".format(exception))
    if cmdline:
        __print_results(results)
    return results


def print_results(results):
    __print_results(results)


def __print_results(areas):
    for area, area_map in areas.items():
        print(area)
        for feature, feature_map in area_map.items():
            print(("  {}".format(feature)))
            for _bp, tests in feature_map.items():
                print(("   {}".format(_bp)))
                # print "{}:{}:{}".format(area, feature, bp)
                for test in tests:
                    print("      - ({}) {} -- [{}]".format(test['current_settings'].get('level'), test['name'],
                                                           ",".join(test['current_settings'].get('tags', []))))
        print("")


def register_ioc_globals(flask_app):  # pylint: disable=unused-argument
    pass


def configure_module(flask_app):  # pylint: disable=unused-argument
    pass
