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
import os
import json
import logging

from rapid.lib.exceptions import InvalidReportException
from rapid.lib.framework.injectable import Injectable
from rapid.master.data.database import execute_db_query

logger = logging.getLogger('rapid')


class ReportDal(Injectable):
    __injectables__ = {'rapid_config': None}

    def __init__(self, rapid_config):
        self._rapid_config = rapid_config
        self._canned_reports = {}
        self._read_report_files()

    def get_canned_report_names(self):
        return self._canned_reports.keys()

    def get_canned_report(self, report_name):
        try:
            report = self._canned_reports[report_name]
            results = []
            count = 0
            for row in execute_db_query(report['sql']):
                column_count = 0
                result = {}
                for header in report['headers']:
                    result[header['attribute']] = row[column_count]
                    column_count += 1
                results.append(result)
            return {'headers': report['headers'], 'results': results}
        except Exception:
            pass
        raise InvalidReportException("Report is not found")

    def _read_report_files(self):
        try:
            for root, dirs, files in os.walk(self._rapid_config.custom_reports_dir):  # pylint: disable=unused-variable
                for filename in files:
                    try:
                        basename = os.path.splitext(filename)
                        with open("{}/{}".format(root, filename)) as tmp_file:
                            self._canned_reports[basename[0]] = json.load(tmp_file)
                            self._canned_reports[basename[0]]['sql'] = self._canned_reports[basename[0]]['sql'].replace('%', '%%')
                    except Exception as exception:
                        logger.error("Was Unable to process the directory defined. {}".format(exception))
        except Exception:
            pass
