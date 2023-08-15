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

from rapid.client import load_parsers
from rapid.client.executor import Executor
from rapid.lib.communication import Communication
from rapid.lib.constants import Constants
from rapid.lib.work_request import WorkRequest
from tests.framework.unit_test import UnitTest


class TestExecutor(UnitTest):
    def setUp(self):
        load_parsers()

    def test_get_command(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Will download remote file when remote: is used.
        :return:
        :rtype:
        """
        work_request = WorkRequest({"action_instance_id": 1,
                                    "cmd": "/bin/sh",
                                    "executable": "{}trial.sh".format(Communication.REMOTE_FILE),
                                    "args": "2>&1"})

        executor = Executor(work_request, None)
        communicator = Mock()
        communicator.get_downloaded_file_name.return_value = "/tmp/rapidci/workspace/trial.sh"

        self.assertEqual(["/bin/sh", "/tmp/rapidci/workspace/trial.sh"], executor.get_command(communicator))

    def test_get_remote_files_invalid_line(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Will download remote file when remote: is used.
        :return:
        :rtype:
        """                                                                               
        with self.assertRaises(Exception) as cm:
            Executor._get_remote_files("This is a test")
        self.assertEqual("list index out of range", str(cm.exception))

    def test_get_remote_files_valid_line(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Will download remote file when remote: is used.
        :return:
        :rtype:
        """
        self.assertEqual(["trial.sh"], Executor._get_remote_files("{}{}".format(Constants.REQUIRED_FILES, "trial.sh")))

    def test_get_results_SUCCESS(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Return codes greater than 0 will result in failure.
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest(), None)

        self.assertEqual("SUCCESS", executor._get_status(0))

    def test_get_results_FAILURE(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Return codes greater than 0 will result in failure.
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest(), None)

        self.assertEqual("FAILED", executor._get_status(1))

    def test_get_results_OVERRIDE(self):
        """
        rapid-unit: Rapid Client:Remote Execution:You can override return codes with different statuses.
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest(), None)
        executor.status_overrides = {4: "GIT_ERROR"}

        self.assertEqual("GIT_ERROR", executor._get_status(4))

    def test_get_parameters(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Parameters can be recorded and passed via pipeline_instance
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest(), None)

        self.assertEqual(["/tmp/testing.txt", "/tmp/*.txt"], executor._get_parameters_files("{}/tmp/testing.txt,/tmp/*.txt".format(Constants.PARAMETERS)))

    def test_get_parameters_error(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Parameters can be recorded and passed via pipeline_instance
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest(), None)

        with self.assertRaises(Exception) as cm:
            executor._get_parameters_files("nothing")
        self.assertEqual("list index out of range", str(cm.exception))

    def test_get_stats(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Statistics can be recorded per pipeline_instance
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest(), None)

        self.assertEqual(['/tmp/testing.txt', '/tmp/*.txt'], executor._get_stats_files("{}/tmp/testing.txt,/tmp/*.txt".format(Constants.STATS)))

    def test_convert_to_dict(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        self.assertEqual({"first": "is good", "second": "is=bad"}, Executor._convert_to_dict(["first=is good", "second=is=bad"]))

    def test_get_results(self):
        """
        rapid-unit: Rapid Client:Can gather test results
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest(), None)
        file_name = '{}/parsers/*.xml'.format(os.path.dirname(os.path.realpath(__file__)))
        self.assertEqual({
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
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest({'action_instance_id': 1, 'pipeline_instance_id': 2, 'environment': {'Something': 'More'}}), None)
        environment = os.environ
        environment.update({'Something': 'More', 'action_instance_id': '1', 'pipeline_instance_id': '2', 'PYTHONUNBUFFERED': 'true'})
        test = executor.get_environment()

        self.assertEqual('More', executor.get_environment()['Something'])
        self.assertEqual('1', executor.get_environment()['action_instance_id'])
        self.assertEqual('2', executor.get_environment()['pipeline_instance_id'])
        self.assertEqual('true', executor.get_environment()['PYTHONUNBUFFERED'])

    def test_verify_work_request_no_action_instance_id(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        work_request = WorkRequest()
        executor = Executor(work_request, "http")

        with self.assertRaises(Exception) as cm:
            executor.verify_work_request()
        self.assertEqual("Invalid action_instance_id", str(cm.exception))

    def test_verify_work_request_no_executable(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        work_request = WorkRequest()
        executor = Executor(work_request, "http")
        work_request.action_instance_id = 1

        with self.assertRaises(Exception) as cm:
            executor.verify_work_request()
        self.assertEqual("Executable not set, nothing to run.", str(cm.exception))

    def test_verify_work_request_no_pipeline_instance_id(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        work_request = WorkRequest()
        executor = Executor(work_request, "http")
        work_request.action_instance_id = 1
        work_request.executable = "something"

        with self.assertRaises(Exception) as cm:
            executor.verify_work_request()
        self.assertEqual("No pipline_instance_id set.", str(cm.exception))

    def test_verify_work_request_no_cmd(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        work_request = WorkRequest()
        executor = Executor(work_request, "http")
        work_request.action_instance_id = 1
        work_request.executable = "something"
        work_request.pipeline_instance_id = 1

        with self.assertRaises(Exception) as cm:
            executor.verify_work_request()
        self.assertEqual("No command was set.", str(cm.exception))

    def test_get_state(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        mock = Mock()
        executor = Executor(mock, "http", logger=Mock())

        self.assertEqual({'analyze_tests': None, 'results_files': [],
             'work_request': mock, 'parameter_files': [],
             'master_uri': 'http', 'thread_id': None,
             'read_pid': None, 'status_overrides': {},
             'pid': None,
             'workspace': os.path.join(tempfile.gettempdir(), 'rapid', 'workspace'),
             'failure_threshold': 0, 'stats_files': [], 'quarantine': None, 'verify_certs': True}, executor.__getstate__())

    def test_get_status_overrides(self):
        """
        rapid-unit: Rapid Client:Remote Execution:You can override return codes with different statuses.
        :return:
        :rtype:
        """
        line = "#{}2:SUCCESS,3:FAILED".format(Constants.STATUS_OVERRIDE)

        self.assertEqual({2: "SUCCESS", 3: "FAILED"}, Executor._get_status_overrides(line))

    def test_get_status_override_no_status(self):
        """
        rapid-unit: Rapid Client:Remote Execution:You can override return codes with different statuses.
        :return:
        :rtype:
        """
        self.assertEqual({}, Executor._get_status_overrides("qwerqwer:qpoiuadsfj"))

    def test_get_status_override_bad_status(self):
        """
        rapid-unit: Rapid Client:Remote Execution:You can override return codes with different statuses.
        :return:
        :rtype:
        """
        self.assertEqual({}, Executor._get_status_overrides("#{}2_SUCCESS,3_FAILED".format(Constants.STATUS_OVERRIDE)))

    @patch("rapid.client.executor.threading")
    def test_start(self, threading):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        executor = Executor(Mock(), "bogus")

        executor.start()

        threading.Thread.assert_called_with(target=executor._start_child_process)

    @patch('rapid.client.executor.threading')
    @patch('rapid.client.executor.Executor._start_child_process')
    def test_start_non_threaded(self, child_process, threading):
        # rapid-unit: Rapid Client:Run Action Instance:Can run an action instance from command line.
        executor = Executor(Mock(), 'bogus')
        executor.start(False)
        self.assertEqual(0, threading.Thread.call_count)
        child_process.assert_called_with()

    def test_get_parameters_no_parameter_files(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Parameters can be recorded and passed via pipeline_instance
        :return:
        :rtype:
        """
        self.assertEqual(None, Executor._get_parameters(None, None))

    @patch("rapid.client.executor.open")
    @patch("rapid.client.executor.glob")
    def test_get_parameters_valid_parameter_files(self, glob, open_mock):
        """
        rapid-unit: Rapid Client:Remote Execution:Parameters can be recorded and passed via pipeline_instance
        :return:
        :rtype:
        """
        glob.glob.return_value = [""]
        open_mock.return_value.__enter__.return_value.readlines.return_value = ["something=12345"]

        self.assertEqual({"something": "12345"}, Executor._get_parameters("", [""]))

    def test_get_stats_no_stats_files(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Statistics can be recorded per pipeline_instance
        :return:
        :rtype:
        """
        self.assertEqual(None, Executor._get_stats(None, None))

    @patch("rapid.client.executor.open")
    @patch("rapid.client.executor.glob")
    def test_get_stats_valid_stats_files(self, glob, open_mock):
        """
        rapid-unit: Rapid Client:Remote Execution:Statistics can be recorded per pipeline_instance
        :return:
        :rtype:
        """
        glob.glob.return_value = [""]
        open_mock.return_value.__enter__.return_value.readlines.return_value = ["something=12345"]

        self.assertEqual({"something": "12345"}, Executor._get_stats("", [""]))

    def test_log(self):
        """
        rapid-unit: Rapid Client:Logging:Logging is formatted a specified way
        :return:
        :rtype:
        """
        mock_logger = Mock()
        Executor._log(1, "Testing", mock_logger)

        mock_logger.info.assert_called_with("__RCI_{}__ - {} - {}".format(1, os.getpid(), "Testing"))

    def test_get_arguments_empty_work_request(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest({'args': None}), "bogus")

        self.assertEqual([], executor.get_arguments())

    def test_get_arguments_from_work_request(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus")

        self.assertEqual(["testing", "arguments"], executor.get_arguments())

    @patch("rapid.client.controllers.work_controller.logger")
    @patch("rapid.client.executor.shutil")
    @patch("rapid.client.executor.os")
    def test_clean_workspace_valid_dir(self, mock_os, mock_shutil, mock_logger):
        """
        rapid-unit: Rapid Client:Remote Execution:Code will execute in sandboxed workspace
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus", workspace="boggus", logger=mock_logger)

        mock_os.sep = '/'
        
        executor.clean_workspace()
        mock_shutil.rmtree.assert_called_with("boggus", ignore_errors=True)

    @patch("rapid.client.controllers.work_controller.logger")
    @patch("rapid.client.executor.shutil")
    @patch("rapid.client.executor.os")
    def test_clean_workspace_valid_dir_exception(self, mock_os, mock_shutil, mock_logger):
        """
        rapid-unit: Rapid Client:Remote Execution:Code will execute in sandboxed workspace
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus", workspace="boggus", logger=mock_logger)

        def throw_exception(*args, **kwargs):
            raise Exception("Should not see this")

        mock_os.sep = '/'
        
        mock_shutil.rmtree = throw_exception
        executor.clean_workspace()

    @patch("rapid.client.executor.os")
    def test_clean_workspace_invalid_dir(self, mock_os):
        """
        rapid-unit: Rapid Client:Remote Execution:Code will execute in sandboxed workspace
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus", workspace="boggus")

        mock_os.path.isdir.return_value = False
        mock_os.sep = '/'

        executor.clean_workspace()
        mock_os.makedirs.assert_called_with("boggus")

    @patch("rapid.client.executor.os")
    def test_clean_workspace_invalid_dir_exception(self, mock_os):
        """
        rapid-unit: Rapid Client:Remote Execution:Code will execute in sandboxed workspace
        :return:
        :rtype:
        """
        executor = Executor(WorkRequest({'args': "testing arguments"}), "bogus", workspace="boggus")
        mock_logger = Mock()
        executor.logger = mock_logger
        self_exception = Exception("Should not see this")

        def throw_exception(*args, **kwargs):
            raise self_exception

        mock_os.makedirs = throw_exception
        mock_os.path.isdir.return_value = False
        mock_os.sep = '/'

        executor.clean_workspace()

        mock_logger.exception.assert_called_with(self_exception)

    def test_get_executable_name_no_remote_file(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        self.assertEqual("filename", Executor._get_executable_name("filename"))

    def test_get_executable_name_with_remote_file(self):
        """
        rapid-unit: Rapid Client:Remote Execution:Can remotely execute code on client
        :return:
        :rtype:
        """
        self.assertEqual("filename", Executor._get_executable_name("{}filename".format(Communication.REMOTE_FILE)))

    def test_get_read_process_output(self):
        """
        rapid-unit: Rapid Client:Logging:Can read the output from external process
        :return:
        :rtype:
        """
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
        """
        rapid-unit: Rapid Client:Logging:Can read the output from external process
        :return:
        :rtype:
        """
        mock_logger = Mock()
        mock_child_process = Mock()

        def readline(*args, **kwargs):
            raise Exception("Shouldn't see this.")

        mock_child_process.stdout.readline = readline

        executor = Executor(WorkRequest(), "bogus", mock_logger)

        executor._read_process_output(mock_logger, mock_child_process)
        mock_logger.info.assert_called_with("__RCI_{}__ - {} - {}".format(None, os.getpid(), "Shouldn't see this."))

    def test_get_name_map(self):
        """
        rapid-unit: Rapid Client:Can gather test results
        :return:
        :rtype:
        """
        executor = Executor(None, None)
        results = {
            'LegacyDateTest::testGetDateDiffString~testGetDateDiffString with data set #0': "success",
            'OfferLettersControllerTest~testSendOfferLetterMissingRequestDataException': "success"
        }
        name_map = executor._get_name_map(results)

        self.assertTrue('testGetDateDiffString with data set #0' in name_map)
        self.assertTrue('testSendOfferLetterMissingRequestDataException' in name_map)

    @patch('rapid.client.executor.Executor.verify_lines')
    def test_check_for_dynamic_config_file(self, verify_lines):
        """
        rapid-unit: Rapid Client:Can gather test results
        :return:
        :rtype:
        """
        executor = Executor(None, None)

        executor.verify_file_lines(['{}bogus2'.format(Constants.PARAMETERS)], None)
        verify_lines.assert_called_with( '{}bogus2'.format(Constants.PARAMETERS), None)

    def test_get_environment_with_unicode_bytes(self):
        executor = Executor(Mock(environment={b'Testing': u'\u2013 Trial and Error'}), None)
        self.assertEqual('– Trial and Error', executor.get_environment()['Testing'])

    @patch('rapid.client.executor.os')
    def test_normalize_workspace_for_windows(self, mock_os):
        mock_os.sep = '\\'
        executor = Executor(None, None, workspace='D:\\testing/another\\foo/bar')
        self.assertEqual('D:\\testing\\another\\foo\\bar', executor._normalize_workspace())

    @patch('rapid.client.executor.os')
    def test_normalize_workspace_for_linux(self, mock_os):
        mock_os.sep = '/'
        executor = Executor(None, None, workspace='/root\\bar/testing\\foo')
        self.assertEqual('/root/bar/testing/foo', executor._normalize_workspace())
