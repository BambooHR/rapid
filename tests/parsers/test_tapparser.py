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
from rapid.client.parsers.tap_parser import TapParser
from rapid.lib.constants import Constants
from tests.framework.unit_test import UnitTest


class TestTapParser(UnitTest):
    def __get_failing_results(self):
        return """Tap
TAP version 13
# APIUtils.getListOnDemandURI
ok 1 - should allow substitution.
ok 2 - should allow empty call.
# APIUtils other methods
ok 3 - getKillOnDemandURI
ok 4 - getScrubbedDbsURI
ok 5 - getQATestMapCoverageURI
ok 6 - getOnDemandPipelineIds
# Utils - FilterPipe
ok 7 - Should filter accross all attributes.
# Utils - EntriesPipe
not ok 8 - Should return key value pairs.
  ---
    operator: deepEqual
    expected: |-
      [ { 0: { id: 'jim' } } ]
    actual: |-
      [ { key: '0', value: { id: 'jim' } }, { key: '1', value: { id: 'sam', val: 'jim' } }, { key: '2', value: { id: 'hello' } } ]
    at: Test.<anonymous> (/units/app/core/lib/utils-test.js:17:7)
  ...
# Run-Stat Tests
ok 9 - should get all action_instances
ok 10 - should be equivalent
ok 11 - Should get all actions, even with partial data.

1..11
# tests 11
# pass  10
# fail  1

# ok"""

    def __get_malformed_results(self):
        return """Tap
TAP version 13
# APIUtils.getListOnDemandURI
ok
ok - missing test number
ok 3
# APIUtils other methods with malformed lines
not ok
not ok - missing test number
not ok 6
  ---
    operator: deepEqual
    expected: |-
      [ { 0: { id: 'jim' } } ]
    actual: |-
      [ { key: '0', value: { id: 'jim' } }, { key: '1', value: { id: 'sam', val: 'jim' } }, { key: '2', value: { id: 'hello' } } ]
    at: Test.<anonymous> (/units/app/core/lib/utils-test.js:17:7)
# Missing closing ... for the above failure
# Utils - FilterPipe
ok 7 - Should filter accross all attributes.
# Utils - EntriesPipe
not ok 8 - Should return key value pairs.
  ---
    operator: deepEqual
    expected: |-
      [ { 0: { id: 'jim' } } ]
    actual: |-
      [ { key: '0', value: { id: 'jim' } }, { key: '1', value: { id: 'sam', val: 'jim' } }, { key: '2', value: { id: 'hello' } } ]
    at: Test.<anonymous> (/units/app/core/lib/utils-test.js:17:7)
  ...
# Run-Stat Tests with incomplete data
ok 9 - should get all action_instances
ok 10 - should be equivalent
not ok 11 - Should get all actions, even with partial data.
# Missing closing ... for the above failure

1..11
# tests 11
# pass  8
# fail  3

# ok"""

    def test_parser_should_have_summary_with_one_failure(self):
        parser = TapParser()
        results = parser.parse(self.__get_failing_results().split("\n"))

        self.assertEqual(1, results['__summary__']['FAILED'])

    def test_parser_should_have_summary_with_10_success(self):
        parser = TapParser()
        results = parser.parse(self.__get_failing_results().split("\n"))

        self.assertEqual(10, results['__summary__']['SUCCESS'])

    def test_parser_should_produce_stacktrace(self):
        parser = TapParser()
        results = parser.parse(self.__get_failing_results().split("\n"))

        self.assertEqual("""  ---
    operator: deepEqual
    expected: |-
      [ { 0: { id: 'jim' } } ]
    actual: |-
      [ { key: '0', value: { id: 'jim' } }, { key: '1', value: { id: 'sam', val: 'jim' } }, { key: '2', value: { id: 'hello' } } ]
    at: Test.<anonymous> (/units/app/core/lib/utils-test.js:17:7)
""", results['Should return key value pairs.']['stacktrace'])

    def test_parser_should_handle_malformed_tap_output(self):
        parser = TapParser()
        results = parser.parse(self.__get_malformed_results().split("\n"))

        self.assertIn('tap_parse_error', results)
        self.assertEqual(Constants.STATUS_FAILED, results['tap_parse_error']['status'])
        self.assertIn('Error parsing TAP data:', results['tap_parse_error']['stacktrace'])
        self.assertGreaterEqual(results['__summary__']['FAILED'], 1)
