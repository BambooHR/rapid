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

parsers = {}


def register(clz):
    parsers[clz.get_type()] = clz
    return clz


def load_parsers():
    from .xunit_parser import XUnitParser
    from .tap_parser import TapParser

    for parser in [XUnitParser, TapParser]:
        register(parser)


def parse_file(lines, parser=None, workspace=None):
    if parser is None and lines[0] and lines[0].strip() in parsers:
        try:
            parser = parsers[lines[0].strip()](workspace=workspace)
            return parser.parse(lines)
        except Exception as exception:
            import traceback
            traceback.print_exc()
            raise exception
    elif parser:
        try:
            return parser.parse(lines, ignore_type_check=True)
        except Exception as exception:
            import traceback
            traceback.print_exc()
            raise exception
    return {}


def get_parser(identifier, workspace=None, failures_only=False, failures_count=False):
    if identifier in parsers:
        return parsers[identifier](workspace=workspace, failures_only=failures_only, failures_count=failures_count)
    return None


class FileWrapper(object):  # pylint: disable=too-few-public-methods
    def __init__(self, workspace, file_definition):
        self.file_name = file_definition
        self.parser = None

        self._workspace = workspace

        self.populate()

    def populate(self):
        try:
            _sp = self.file_name.split('#')
            self.file_name = _sp[1]

            identifier = _sp[0]
            failures_only = False
            failures_count = False
            try:
                failures_only = _sp[0].split('-')[1] == Constants.FAILURES
                failures_count = _sp[0].split('-')[1] == Constants.FAILURES_COUNT
                identifier = _sp[0].split('-')[0]
            except (IndexError, AttributeError):
                pass

            self.parser = get_parser(identifier, self._workspace, failures_only, failures_count)
        except Exception:  # pylint: disable=broad-except
            pass
