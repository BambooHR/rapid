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

parsers = {}


def register(clz):
    parsers[clz.get_type()] = clz
    return clz


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


def get_parser(identifier, workspace=None, failures_only=False):
    if identifier in parsers:
        return parsers[identifier](workspace=workspace, failures_only=failures_only)
    return None


from XUnitParser import XUnitParser
from TapParser import TapParser