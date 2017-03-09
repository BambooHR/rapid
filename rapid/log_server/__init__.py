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

from flask import Flask
from flask.wrappers import Response
import subprocess


app = Flask("rapidci_logger")
app.rapid_config = {'_is': 'logger'}
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

logger = logging.getLogger("rapid")
logger.addHandler(handler)
logger.setLevel(logging.INFO)


UWSGI = False
try:
    import uwsgi
    UWSGI = True
except ImportError:
    pass


def _read_log(grep):
    try:
        lines = []
        string_grep = "__RCI_{}__".format(grep)

        found_output = False
        process = subprocess.Popen("grep {} {}/*.log".format(string_grep, app.log_dir).split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        gz_files = glob.glob("{}/*.gz".format(app.log_dir))
        log_files = glob.glob("{}/*.log".format(app.log_dir))

        for check in [{'cmd': 'grep {} {}', 'files': ' '.join(log_files)}, {'cmd': 'zgrep {} {}', 'files': ' '.join(gz_files)}]:
            cmd = check['cmd'].format(string_grep, check['files'])
            process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
            for line in iter(process.stdout.readline, ''):
                found_output = True
                yield line

            if found_output:
                break
    except Exception as exception:
        import traceback
        traceback.print_exc()
        logger.error(exception)
        pass


def grep_log(grep):
    return Response(_read_log(grep), content_type='text/plain')


def configure_application(flask_app, args):
    flask_app.add_url_rule("/log/<path:grep>", 'logging', grep_log, methods=['GET'])

    if args.log_dir:
        flask_app.log_dir = args.log_dir

