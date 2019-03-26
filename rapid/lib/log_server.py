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
import logging
import glob
import os
import subprocess

from flask import Response
logger = logging.getLogger('rapid')


class LogServer(object):
    def __init__(self, log_dir=None):
        self.log_dir = log_dir

    def _read_log(self, grep):
        if self.log_dir is None:
            yield "The logging directory is not configured."

        try:
            string_grep = "__RCI_{}__".format(grep)

            found_output = False
            gz_files = glob.glob(os.path.join(self.log_dir, "*.gz"))
            log_files = glob.glob(os.path.join(self.log_dir, "*.log"))

            if log_files:
                for check in [{'cmd': 'grep -a {} {}', 'files': ' '.join(log_files)}, {'cmd': 'zgrep -a {} {}', 'files': ' '.join(gz_files)}]:
                    cmd = check['cmd'].format(string_grep, check['files'])
                    process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    for line in iter(process.stdout.readline, ''):
                        found_output = True
                        yield line

                    if found_output:
                        break
            else:
                yield ""
        except Exception as exception:  # pylint: disable=broad-except
            logger.exception(exception)
        yield ""

    def configure_application(self, flask_app):
        flask_app.add_url_rule("/log/<path:grep>", 'logging', self.grep_log, methods=['GET'])

        if self.log_dir:
            flask_app.log_dir = self.log_dir

    def grep_log(self, grep):
        return Response(self._read_log(grep), content_type='text/plain')
