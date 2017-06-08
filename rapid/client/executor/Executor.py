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

import glob
import logging
import os
import shutil
import subprocess
import threading

from rapid import testmapper
from rapid.client.communicator.ClientCommunicator import ClientCommunicator
from rapid.lib.Communication import Communication
from rapid.lib.Constants import Constants
from rapid.lib.Exceptions import ThresholdException, ResultsFileNotFoundException, ResultsFileNotParsedException
from rapid.lib.Features import Features
from rapid.lib.StoreService import StoreService
from rapid.lib.Utils import deep_merge

try:
    import uwsgi
except:
    pass


class Executor(object):
    def __init__(self, work_request, master_uri, logger=None, workspace='/tmp/rapidci/workspace', quarantine=None, verify_certs=True, rapid_config=None):
        """

        :param work_request:
        :param master_uri:
        :param logger:
        :param workspace:
        :param quarantine:
        :param verify_certs:
        :type rapid_config: :class:
        :return:
        """
        self.thread = None
        self.reading_thread = None
        self.thread_id = None
        self.read_pid = None
        self.work_request = work_request
        self.child_process = None
        self.workspace = workspace
        self.master_uri = master_uri
        self.reading_thread = None
        self.logger = logger
        self.status_overrides = {}
        self.results_files = []
        self.parameter_files = []
        self.stats_files = []
        self.quarantine = quarantine
        self.failure_threshold = 0
        self.verify_certs = verify_certs
        self.rapid_config = rapid_config
        self.analyze_tests = None

        if self.logger is None:
            self.logger = self._create_logger()

    def __getstate__(self):
        state = self.__dict__.copy()
        for attribute in ['logger', 'thread', 'reading_thread', 'child_process', 'rapid_config']:
            if attribute in state:
                del state[attribute]

        return state

    def verify_work_request(self):
        if not self.work_request.action_instance_id:
            raise Exception("Invalid action_instance_id")
        if not self.work_request.executable:
            raise Exception("Executable not set, nothing to run.")
        if not self.work_request.pipeline_instance_id:
            raise Exception("No pipline_instance_id set.")
        if not self.work_request.cmd:
            raise Exception("No command was set.")

    def _create_logger(self):
        logger = logging.getLogger("rapid")
        logger.setLevel(logging.INFO)
        return logger

    def start(self):
        """
        Spin off a process that will execute and run the given work request.
        :return:
        """
        self.thread = threading.Thread(target=self._start_child_process)
        self.thread.daemon = True
        self.thread.start()

    def _start_child_process(self):
        """
        Start a child process with the command.
        :return:
        """
        communicator = ClientCommunicator(self.master_uri,
                                          self.quarantine,
                                          verify_certs=self.verify_certs,
                                          get_files_auth=self.rapid_config.get_files_basic_auth)

        # Cleanup first
        self.workspace = "{}/{}".format(self.workspace, self.work_request.action_instance_id)
        self.clean_workspace()

        env = self.get_environment()
        try:
            command = self.get_command(communicator)
            command.extend(self.get_arguments())

            # Check and download required files that will execute in command.
            try:
                self._download_required_files([self.work_request.executable], communicator, self.logger)
            except Exception as exception:
                self.logger.exception(exception)
                raise exception

            stdout = None
            stderr = None
            if self.logger:
                stdout = subprocess.PIPE
                stderr = subprocess.STDOUT

            self.child_process = subprocess.Popen(command, cwd=self.workspace, env=env, stderr=stderr, stdout=stdout)
            self.pid = self.child_process.pid

            StoreService.save_executor(self)

            # wait for the process to finish
            self.reading_thread = threading.Thread(target=self._read_process_output, args=(self.logger, self.child_process))
            self.reading_thread.daemon = True
            self.reading_thread.start()

            self.child_process.wait()

            self._finalize_run(communicator)
        except (BaseException, Exception) as exception:
            self.logger.exception(exception)
            communicator.send_done(self.work_request.action_instance_id, 'FAILED', None, None, None, self.logger)
        finally:
            self.clean_workspace()

    def _finalize_run(self, communicator):
        # Send results to master
        # Parse and Send parameters
        status = self._get_status(self.child_process.returncode)
        results = None
        try:
            results = self._get_results(self.workspace, self.results_files)
            if results:
                if Constants.RESULTS_SUMMARY in results and 'FAILED' in results[Constants.RESULTS_SUMMARY] and results[Constants.RESULTS_SUMMARY]['FAILED'] > self.failure_threshold:
                    raise ThresholdException("Failure threshold was exceeded")

        except ThresholdException as exception:
            status = 'UNSTABLE'
        except ResultsFileNotFoundException as exception:
            self.logger.error("Expected ResultsFile was not where specified.")
            status = 'FAILED'
        except ResultsFileNotParsedException:
            self.logger.error("Expected ResultsFile was not parsed.")
            status = 'FAILED'
        finally:
            parameters = Executor._get_parameters(self.workspace, self.parameter_files)
            stats = Executor._get_stats(self.workspace, self.stats_files)

            self.logger.info("Sending the Done command!")
            communicator.send_done(self.work_request.action_instance_id, status, parameters, stats, results, self.logger)

        try:
            name_map = self._get_name_map(results)
            test_analysis = self._get_test_analysis(self.workspace, self.analyze_tests, name_map)

            if test_analysis is not None:
                communicator.send_test_analysis(self.work_request.pipeline_instance_id, test_analysis, self.logger)
        except Exception as exception:
            self.logger.error(exception)

        # Clear only after having sent the done.
        StoreService.clear_executor(self)

    def _get_name_map(self, results):
        name_map = {}
        if results:
            for name in results.keys():
                sp = name.split('~')
                last = sp[-1]
                name_map[last] = name
        return name_map

    @staticmethod
    def _get_parameters(workspace, parameter_files):
        if parameter_files:
            parameters = {}
            for glob_tmp in parameter_files:
                for parameter_file in glob.glob("{}/{}".format(workspace, glob_tmp)):
                    with open(parameter_file) as glob_file:
                        lines = glob_file.readlines()
                        parameters.update(Executor._convert_to_dict(lines))

            return parameters
        return None

    @staticmethod
    def _get_stats(workspace, stats_files):
        if stats_files:
            stats = {}
            for glob_tmp in stats_files:
                for stats_file in glob.glob("{}/{}".format(workspace, glob_tmp)):
                    with open(stats_file) as glob_file:
                        lines = glob_file.readlines()
                        stats.update(Executor._convert_to_dict(lines))
            return stats
        return None

    @staticmethod
    def _convert_to_dict(lines):
        return dict((k.strip(), v.strip()) for k, v in
                    (item.split('=', 1) for item in lines))

    def _get_results(self, workspace, results_files):
        if results_files:
            # Wire in the registered parsers.
            results = {}
            from ..parsers import parse_file, get_parser

            for file_glob in results_files:
                glob_tmp = file_glob
                selected_parser = None

                if '#' in file_glob:
                    sp = file_glob.split('#')
                    glob_tmp = sp[1]

                    identifier = sp[0]
                    failures_only = False
                    try:
                        failures_only = sp[0].split('-')[1] == 'failures'
                        identifier = sp[0].split('-')[0]
                    except:
                        pass

                    selected_parser = get_parser(identifier, self.workspace, failures_only)

                file_was_read = False
                for results_file in glob.glob("{}/{}".format(workspace, glob_tmp)):
                    file_was_read = True
                    with open(results_file) as glob_file:
                        try:
                            lines = glob_file.read().splitlines(True)
                            parsed_results = parse_file(lines, selected_parser)

                            summary = parsed_results[Constants.RESULTS_SUMMARY] if Constants.RESULTS_SUMMARY in parsed_results else None
                            if summary is not None:
                                if Constants.RESULTS_SUMMARY not in results:
                                    results[Constants.RESULTS_SUMMARY] = summary
                                else:
                                    for (key,value) in summary.items():
                                        results[Constants.RESULTS_SUMMARY][key] += value
                                del parsed_results[Constants.RESULTS_SUMMARY]

                            results.update(parsed_results)
                        except:
                            raise ResultsFileNotParsedException("Result file did not parse.")

                if not file_was_read:
                    raise ResultsFileNotFoundException("Results file not read.")

            return results
        return None

    def _get_status(self, return_code):
        status = 'SUCCESS'
        if return_code > 0:
            status = 'FAILED'
            status = self.status_overrides[return_code] if return_code in self.status_overrides else status
        return status

    def _read_process_output(self, logger, child_process):
        try:
            for line in iter(child_process.stdout.readline, b''):
                self._log(self.work_request.action_instance_id, line.strip(), logger)
            self._log(self.work_request.action_instance_id, "Cleaning up thread.", logger)
        except Exception as exception:
            self._log(self.work_request.action_instance_id, exception.message, logger)

    @staticmethod
    def _get_test_analysis(workspace, test_analysis, name_map):
        results = {}
        if isinstance(test_analysis, str):
            for dirname in glob.glob("{}/{}".format(workspace, test_analysis)):
                results = deep_merge(results, testmapper.process_directory(workspace, dirname, name_map=name_map))
        elif isinstance(test_analysis, list):
            for glob_tmp in test_analysis:
                for filename in glob.glob("{}/{}".format(workspace, glob_tmp)):
                    results = deep_merge(results, testmapper.process_directory(workspace, filename, name_map=name_map))
        return results

    @staticmethod
    def _log(action_instance_id, message, logger):
        logger.info("__RCI_{}__ - {} - {}".format(action_instance_id, os.getpid(), message))

    def get_environment(self):
        env = {}
        for key in os.environ:
            env[key] = os.environ[key]

        if self.work_request.environment:
            env.update(self.work_request.environment)
        env['PYTHONUNBUFFERED'] = "true"
        env['pipeline_instance_id'] = str(self.work_request.pipeline_instance_id)
        env['action_instance_id'] = str(self.work_request.action_instance_id)
        env['workflow_instance_id'] = str(self.work_request.workflow_instance_id)
        env['slice'] = str(self.work_request.slice)
        env['RAPID_FEATURES'] = ",".join(Features.get_enabled_features())
        env['WORKSPACE'] = self.workspace

        return env

    def get_command(self, communicator):
        """
        :type communicator: :class:`rapid.client.communicator.ClientCommunicator.ClientCommunicator`
        :return:
        """
        command = []
        if self.work_request.cmd:
            command.append(self.work_request.cmd)
        if self.work_request.executable:
            command.append(communicator.get_downloaded_file_name(self.workspace,
                                                                 self._get_executable_name(self.work_request.executable)))
        return command

    def get_arguments(self):
        arguments = []
        if self.work_request.args:
            arguments.extend(self.work_request.args.split(' '))
        return arguments

    def clean_workspace(self):
        if os.path.isdir(self.workspace):
            try:
                Executor._log(self.work_request.action_instance_id, "{} - removing workspace".format(self.workspace), self.logger)
                shutil.rmtree(self.workspace, ignore_errors=True)
            except:
                pass
        else:
            try:
                os.mkdir(self.workspace)
            except Exception as exception:
                Executor._log(self.work_request.action_instance_id, "{} - Workspace was unable to be created.".format(self.workspace), self.logger)
                self.logger.exception(exception)

    @staticmethod
    def _get_executable_name(file_name):
        if file_name and file_name.startswith(Communication.REMOTE_FILE):
            return file_name.split(Communication.REMOTE_FILE, 2)[1]
        return file_name

    def _download_required_files(self, file_names, communicator, logger, is_from_file=False, files_downloaded=[]):
        """
        Download the file, if a remote file, and then determine if there are any required files that need to be
        downloaded.
        :param list file_names: list of file names
        :param ClientCommunicator communicator: Communicator to download
        :return:
        """
        if not isinstance(file_names, list):
            raise Exception("file_names is not a list")

        if file_names:
            for file_name in file_names:
                if Communication.REMOTE_FILE in file_name or is_from_file:
                    Executor._log(self.work_request.action_instance_id, "Downloading file: {}".format(file_name),
                                  logger)
                    true_file_name = Executor._get_executable_name(file_name)
                    files_downloaded.append(file_name)
                    with open(communicator.get_file(self.workspace, true_file_name, logger), 'r') as file:
                        lines = file.readlines()
                        self._download_by_lines(lines,
                                                communicator,
                                                logger,
                                                files_downloaded)

    def verify_lines(self, line, logger):
        try:
            results_files = Executor._get_results_files(line)
            self.results_files.extend(results_files)
        except Exception as exception:
            logger.debug(exception)
        try:
            parameters_file = Executor._get_parameters_files(line)
            self.parameter_files.extend(parameters_file)
        except Exception as exception:
            logger.debug(exception)
        try:
            stats_file = Executor._get_stats_files(line)
            self.stats_files.extend(stats_file)
        except Exception as exception:
            logger.debug(exception)

        try:
            threshold = Executor._get_failure_threshold(line)[0]
            self.failure_threshold = int(threshold)
        except Exception as exception:
            logger.debug(exception)

        try:
            self.status_overrides.update(Executor._get_status_overrides(line))
        except Exception as exception:
            logger.debug(exception)

        try:
            if self.analyze_tests is None:
                self.analyze_tests = Executor._get_analyze_tests(line)
            else:
                self.analyze_tests.extend(Executor._get_analyze_tests(line))
        except Exception as exception:
            logger.debug(exception)

    def _download_by_lines(self, lines, communicator, logger, files_downloaded=[]):
        """
        Download files by recursing list of lines.
        :param list lines:
        :param ClientCommunicator communicator:
        :return:
        """
        for line in lines:
            try:
                self._download_required_files(Executor._get_remote_files(line),
                                              communicator,
                                              logger,
                                              is_from_file=True,
                                              files_downloaded=files_downloaded)
            except:
                logger.debug("Line returned nothing for required files: {}".format(line))

            self.verify_lines(line, logger)

    @staticmethod
    def _get_analyze_tests(line):
        """
        Splits a line for Constants.REQUIRED_FILES and ',' and returns the split.
        :param line: line from a file to split
        :return: list from the split
        :raises  IndexError if line doesn't contain Constants.REQUIRED_FILES
        """
        return Executor._get_split_string(line, Constants.ANALYZE_TESTS)


    @staticmethod
    def _get_remote_files(line):
        """
        Splits a line for Constants.REQUIRED_FILES and ',' and returns the split.
        :param line: line from a file to split
        :return: list from the split
        :raises  IndexError if line doesn't contain Constants.REQUIRED_FILES
        """
        return Executor._get_split_string(line, Constants.REQUIRED_FILES)

    @staticmethod
    def _get_results_files(line):
        """
        Splits a line from Constants.RESULTS_FILES and ',' and returns the split.
        :param line: line from a file to split
        :return: list from the split
        :raises IndexError if line doesn't contain Constants.RESULTS
        """
        return Executor._get_split_string(line, Constants.RESULTS)

    @staticmethod
    def _get_stats_files(line):
        """
        Splits a line from Constants.STATS_FILES and ',' and returns the split
        :param line: line from a file to split
        :return: list from a the split
        """
        return Executor._get_split_string(line, Constants.STATS)

    @staticmethod
    def _get_parameters_files(line):
        """
        Splits a line from Constants.PARAMETERS and ',' and returns the split
        :param line: line to split
        :return: list from the split
        :raises IndexError if line doesn't contain Constants.PARAMETERS
        """
        return Executor._get_split_string(line, Constants.PARAMETERS)

    @staticmethod
    def _get_failure_threshold(line):
        return Executor._get_split_string(line, Constants.THRESHOLD)

    @staticmethod
    def _get_status_overrides(line):
        overrides = {}
        try:
            for override in Executor._get_split_string(line, Constants.STATUS_OVERRIDE):
                sp = override.split(':')
                if len(sp) > 1:
                    overrides[int(sp[0])] = sp[1]
        except:
            pass
        return overrides

    @staticmethod
    def _get_split_string(line, constant):
        return line.strip().split(constant)[1].split(",")

