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
import pprint
from unittest import TestCase
from nose.tools import eq_
from rapid.client.parsers.XUnitParser import XUnitParser


class TestXunitParser(TestCase):

    def setUp(self):
        self.example = """XUnit
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
   <testsuite name="JUnitXmlReporter" errors="0" tests="0" failures="0" time="0" timestamp="2013-05-24T10:23:58" />
   <testsuite name="JUnitXmlReporter.constructor" errors="0" skipped="1" tests="3" failures="1" time="0.006" timestamp="2013-05-24T10:23:58">
      <properties>
         <property name="java.vendor" value="Sun Microsystems Inc." />
         <property name="compiler.debug" value="on" />
         <property name="project.jdk.classpath" value="jdk.classpath.1.6" />
      </properties>
      <testcase classname="JUnitXmlReporter.constructor" name="should default path to an empty string" time="0.006">
         <failure message="test failure">Assertion failed</failure>
      </testcase>
      <testcase classname="JUnitXmlReporter.constructor" name="should default consolidate to true" time="0">
         <skipped />
      </testcase>
      <testcase classname="JUnitXmlReporter.constructor" name="should default useDotNotation to true" time="0" />
      <testcase classname="tests.api.routing.test_api_routing.TestAPIRouting" name="test_configure_routing_features_enabled" time="0.001"><failure type="exceptions.AssertionError" message="13 != 14"><![CDATA[Traceback (most recent call last):
  File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/unittest/case.py", line 331, in run
 testMethod()
  File "/private/tmp/rapidci/workspace/123145312403456/cihub/tests/api/routing/test_api_routing.py", line 29, in test_configure_routing_features_enabled
     eq_(13, flask_app.add_url_rule.call_count)
  File "/private/tmp/rapidci/workspace/123145312403456/cihub/env/lib/python2.7/site-packages/nose/tools/trivial.py", line 29, in eq_
    raise AssertionError(msg or "%r != %r" % (a, b))
 AssertionError: 13 != 14
]]></failure></testcase>
   </testsuite>
</testsuites>
        """

    def test_get_all_testcases(self):
        parser = XUnitParser()

        results = parser.parse(self.example.split("\n"))
        testing = {
            'JUnitXmlReporter.constructor~should default path to an empty string': {
                'status': 'FAILED',
                'stacktrace': 'Assertion failed',
                'time': '0.006'
            },
            'JUnitXmlReporter.constructor~should default consolidate to true': {
                'status': 'SKIPPED',
                'time': '0'
            },
            'JUnitXmlReporter.constructor~should default useDotNotation to true': {
                'status': 'SUCCESS',
                'time': '0'
            },
            'tests.api.routing.test_api_routing.TestAPIRouting~test_configure_routing_features_enabled': {
                'status': 'FAILED',
                'time': '0.001',
                'stacktrace': 'Traceback (most recent call last):  File "/System/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/unittest/case.py", line 331, in run testMethod()  File "/private/tmp/rapidci/workspace/123145312403456/cihub/tests/api/routing/test_api_routing.py", line 29, in test_configure_routing_features_enabled     eq_(13, flask_app.add_url_rule.call_count)  File "/private/tmp/rapidci/workspace/123145312403456/cihub/env/lib/python2.7/site-packages/nose/tools/trivial.py", line 29, in eq_    raise AssertionError(msg or "%r != %r" % (a, b)) AssertionError: 13 != 14'
            },
            '__summary__': {'FAILED': 2, 'SKIPPED': 1, 'SUCCESS': 1}
        }
        pprint.pprint(testing.keys())
        pprint.pprint(results.keys())
        eq_(testing, results)

    def test_bogus_lines(self):
        parser = XUnitParser()

        with self.assertRaises(Exception) as cm:
            parser.parse(['asfqwerf'])
        eq_('Invalid first line identifier', cm.exception.message)

    def test_nothing_tested(self):
        parser = XUnitParser()

        eq_({'__summary__': {'FAILED': 0, 'SKIPPED': 0, 'SUCCESS': 0}}, parser.parse(['XUnit', '<testsuites></testsuites>']))

    def test_workspace_replace(self):
        parser = XUnitParser('/home/trial')

        eq_({'__summary__': {'FAILED': 1, 'SKIPPED': 0, 'SUCCESS': 0}, '/testing.php~should default path to an empty string': {'status': 'FAILED', 'stacktrace': 'Assertion failed', 'time': '0.006'}}, parser.parse(['<testsuite name="trial">', '<testcase classname="/home/trial/testing.php" name="/home/trialshould default path to an empty string" time="0.006">', '<failure message="test failure">Assertion failed</failure>', '</testcase>', "</testsuite>"], True))
