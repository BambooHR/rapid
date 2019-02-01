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
import tempfile

from mock.mock import Mock, patch
from nose.tools import eq_
from unittest import TestCase

from nose.tools.trivial import ok_

from rapid.client.executor import Executor
from rapid.lib.Communication import Communication
from rapid.lib.Constants import Constants
from rapid.lib.WorkRequest import WorkRequest


class TestExecutor(TestCase):

    def test_get_command(self):
        work_request = WorkRequest({"action_instance_id": 1,
                                    "cmd": "/bin/sh",
                                    "executable": "{}trial.sh".format(Communication.REMOTE_FILE),
                                    "args": "2>&1"})

        executor = Executor(work_request, None)
        communicator = Mock()
        communicator.get_downloaded_file_name.return_value = "/tmp/rapidci/workspace/trial.sh"

        eq_(["/bin/sh", "/tmp/rapidci/workspace/trial.sh"], executor.get_command(communicator))

    def test_get_remote_files_invalid_line(self):
        with self.assertRaises(Exception) as cm:
            Executor._get_remote_files("This is a test")
        self.assertEqual("list index out of range", cm.exception.message)

    def test_get_remote_files_valid_line(self):
        self.assertEqual(["trial.sh"], Executor._get_remote_files("{}{}".format(Constants.REQUIRED_FILES, "trial.sh")))

    def test_get_results_SUCCESS(self):
        executor = Executor(WorkRequest(), None)

        eq_("SUCCESS", executor._get_status(0))

    def test_get_results_FAILURE(self):
        executor = Executor(WorkRequest(), None)

        eq_("FAILED", executor._get_status(1))

    def test_get_results_OVERRIDE(self):
        executor = Executor(WorkRequest(), None)
        executor.status_overrides = {4: "GIT_ERROR"}

        eq_("GIT_ERROR", executor._get_status(4))

    def test_get_parameters(self):
        executor = Executor(WorkRequest(), None)

        eq_(["/tmp/testing.txt", "/tmp/*.txt"], executor._get_parameters_files("{}/tmp/testing.txt,/tmp/*.txt".format(Constants.PARAMETERS)))

    def test_get_parameters_error(self):
        executor = Executor(WorkRequest(), None)

        with self.assertRaises(Exception) as cm:
            executor._get_parameters_files("nothing")
        self.assertEqual("list index out of range", cm.exception.message)

    def test_get_stats(self):
        executor = Executor(WorkRequest(), None)

        eq_(['/tmp/testing.txt', '/tmp/*.txt'], executor._get_stats_files("{}/tmp/testing.txt,/tmp/*.txt".format(Constants.STATS)))

    def test_convert_to_dict(self):
        eq_({"first": "is good", "second": "is=bad"}, Executor._convert_to_dict(["first=is good", "second=is=bad"]))

    def test_get_results(self):
        executor = Executor(WorkRequest(), None)
        file_name = '{}/parsers/*.xml'.format(os.path.dirname(os.path.realpath(__file__)))

        eq_({
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
            '__summary__': {'FAILED': 1, 'SKIPPED': 1, 'SUCCESS': 1, Constants.FAILURES_COUNT: False}}, executor._get_results('/', [file_name]))

    def test_get_environment(self):
        executor = Executor(WorkRequest({'action_instance_id': 1, 'pipeline_instance_id': 2, 'environment': {'Something': 'More'}}), None)
        environment = os.environ
        environment.update({'Something': 'More', 'action_instance_id': '1', 'pipeline_instance_id': '2', 'PYTHONUNBUFFERED': 'true'})
        test = executor.get_environment()

        eq_('More', executor.get_environment()['Something'])
        eq_('1', executor.get_environment()['action_instance_id'])
        eq_('2', executor.get_environment()['pipeline_instance_id'])
        eq_('true', executor.get_environment()['PYTHONUNBUFFERED'])


    def test_verify_work_request_no_action_instance_id(self):
        work_request = WorkRequest()
        executor = Executor(work_request, "http")

        with self.assertRaises(Exception) as cm:
            executor.verify_work_request()
        self.assertEqual("Invalid action_instance_id", cm.exception.message)

    def test_verify_work_request_no_executable(self):
        work_request = WorkRequest()
        executor = Executor(work_request, "http")
        work_request.action_instance_id = 1

        with self.assertRaises(Exception) as cm:
            executor.verify_work_request()
        self.assertEqual("Executable not set, nothing to run.", cm.exception.message)

    def test_verify_work_request_no_pipeline_instance_id(self):
        work_request = WorkRequest()
        executor = Executor(work_request, "http")
        work_request.action_instance_id = 1
        work_request.executable = "something"

        with self.assertRaises(Exception) as cm:
            executor.verify_work_request()
        self.assertEqual("No pipline_instance_id set.", cm.exception.message)

    def test_verify_work_request_no_cmd(self):
        work_request = WorkRequest()
        executor = Executor(work_request, "http")
        work_request.action_instance_id = 1
        work_request.executable = "something"
        work_request.pipeline_instance_id = 1

        with self.assertRaises(Exception) as cm:
            executor.verify_work_request()
        self.assertEqual("No command was set.", cm.exception.message)

    def test_get_state(self):
        mock = Mock()
        executor = Executor(mock, "http", logger=Mock())

        eq_({'analyze_tests': None, 'results_files': [],
             'work_request': mock, 'parameter_files': [],
             'master_uri': 'http', 'thread_id': None,
             'read_pid': None, 'status_overrides': {},
             'workspace': os.path.join(tempfile.gettempdir(), 'rapid', 'workspace'),
             'failure_threshold': 0, 'stats_files': [], 'quarantine': None, 'verify_certs': True}, executor.__getstate__())

    def test_get_status_overrides(self):
        line = "#{}2:SUCCESS,3:FAILED".format(Constants.STATUS_OVERRIDE)

        eq_({2: "SUCCESS", 3: "FAILED"}, Executor._get_status_overrides(line))

    def test_get_status_override_no_status(self):
        eq_({}, Executor._get_status_overrides("qwerqwer:qpoiuadsfj"))

    def test_get_status_override_bad_status(self):
        eq_({}, Executor._get_status_overrides("#{}2_SUCCESS,3_FAILED".format(Constants.STATUS_OVERRIDE)))

    @patch("rapid.client.executor.Executor.threading")
    def test_start(self, threading):
        executor = Executor(Mock(), "bogus")

        executor.start()

        threading.Thread.assert_called_with(target=executor._start_child_process)

    def test_get_parameters_no_parameter_files(self):
        eq_(None, Executor._get_parameters(None, None))

    @patch("rapid.client.executor.Executor.open")
    @patch("rapid.client.executor.Executor.glob")
    def test_get_parameters_valid_parameter_files(self, glob, open_mock):
        glob.glob.return_value = [""]
        open_mock.return_value.__enter__.return_value.readlines.return_value = ["something=12345"]

        eq_({"something": "12345"}, Executor._get_parameters("", [""]))

    def test_get_stats_no_stats_files(self):
        eq_(None, Executor._get_stats(None, None))

    @patch("rapid.client.executor.Executor.open")
    @patch("rapid.client.executor.Executor.glob")
    def test_get_stats_valid_stats_files(self, glob, open_mock):
        glob.glob.return_value = [""]
        open_mock.return_value.__enter__.return_value.readlines.return_value = ["something=12345"]

        eq_({"something": "12345"}, Executor._get_stats("", [""]))

    def test_log(self):
        mock_logger = Mock()
        Executor._log(1, "Testing", mock_logger)

        mock_logger.info.assert_called_with("__RCI_{}__ - {} - {}".format(1, os.getpid(), "Testing"))

    def test_get_arguments_empty_work_request(self):
        executor = Executor(WorkRequest({'args': None}), "bogus")

        eq_([], executor.get_arguments())

    def test_get_arguments_from_work_request(self):
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus")

        eq_(["testing", "arguments"], executor.get_arguments())

    @patch("rapid.client.controllers.work_controller.logger")
    @patch("rapid.client.executor.Executor.shutil")
    @patch("rapid.client.executor.Executor.os")
    def test_clean_workspace_valid_dir(self, mock_os, mock_shutil, mock_logger):
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus", workspace="boggus", logger=mock_logger)

        executor.clean_workspace()
        mock_shutil.rmtree.assert_called_with("boggus", ignore_errors=True)

    @patch("rapid.client.controllers.work_controller.logger")
    @patch("rapid.client.executor.Executor.shutil")
    @patch("rapid.client.executor.Executor.os")
    def test_clean_workspace_valid_dir_exception(self, mock_os, mock_shutil, mock_logger):
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus", workspace="boggus", logger=mock_logger)

        def throw_exception(*args, **kwargs):
            raise Exception("Should not see this")

        mock_shutil.rmtree = throw_exception
        executor.clean_workspace()

    @patch("rapid.client.executor.Executor.os")
    def test_clean_workspace_invalid_dir(self, mock_os):
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus", workspace="boggus")

        mock_os.path.isdir.return_value = False

        executor.clean_workspace()
        mock_os.mkdir.assert_called_with("boggus")

    @patch("rapid.client.executor.Executor.os")
    def test_clean_workspace_invalid_dir_exception(self, mock_os):
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus", workspace="boggus")
        mock_logger = Mock()
        executor.logger = mock_logger
        self_exception = Exception("Should not see this")

        def throw_exception(*args, **kwargs):
            raise self_exception

        mock_os.mkdir = throw_exception
        mock_os.path.isdir.return_value = False

        executor.clean_workspace()

        mock_logger.exception.assert_called_with(self_exception)

    def test_get_executable_name_no_remote_file(self):
        eq_("filename", Executor._get_executable_name("filename"))

    def test_get_executable_name_with_remote_file(self):
        eq_("filename", Executor._get_executable_name("{}filename".format(Communication.REMOTE_FILE)))

    def test_get_read_process_output(self):
        mock_logger = Mock()
        mock_child_process = Mock()

        results = ["testing", b'']

        def readline(*args, **kwargs):
            return results.pop(0)

        mock_child_process.stdout.readline = readline

        executor = Executor(WorkRequest(), "bogus", mock_logger)

        executor._read_process_output(mock_logger, mock_child_process)
        mock_logger.info.assert_called_with("__RCI_{}__ - {} - {}".format(None, os.getpid(), "Cleaning up thread."))

    def test_get_read_process_output_with_exception(self):
        mock_logger = Mock()
        mock_child_process = Mock()

        def readline(*args, **kwargs):
            raise Exception("Shouldn't see this.")

        mock_child_process.stdout.readline = readline

        executor = Executor(WorkRequest(), "bogus", mock_logger)

        executor._read_process_output(mock_logger, mock_child_process)
        mock_logger.info.assert_called_with("__RCI_{}__ - {} - {}".format(None, os.getpid(), "Shouldn't see this."))

    def test_get_name_map(self):
        executor = Executor(None, None)
        results = {
            'LegacyDateTest::testGetDateDiffString~testGetDateDiffString with data set #0': "success",
            'OfferLettersControllerTest~testSendOfferLetterMissingRequestDataException': "success"
        }
        name_map = executor._get_name_map(results)

        ok_('testGetDateDiffString with data set #0' in name_map)
        ok_('testSendOfferLetterMissingRequestDataException' in name_map)

    @patch('rapid.client.executor.Executor.Executor.verify_lines')
    def test_check_for_dynamic_config_file(self, verify_lines):
        executor = Executor(None, None)

        executor.verify_file_lines(['{}bogus2'.format(Constants.PARAMETERS)], None)
        verify_lines.assert_called_with( '{}bogus2'.format(Constants.PARAMETERS), None)
