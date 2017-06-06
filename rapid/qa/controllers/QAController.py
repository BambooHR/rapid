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

from flask.globals import request
from werkzeug.exceptions import HTTPException

from rapid.qa.QaService import QaService
from rapid.lib import api_key_required, json_response
from rapid.lib.framework.Injectable import Injectable

logger = logging.getLogger("rapid")


class QAController(Injectable):
    __injectables__ = {'qa_service': QaService}

    def __init__(self, qa_service):
        """

        :param qa_service:
        :type qa_service: QaService
        """
        self.app = None
        self.qa_service = qa_service

    def register_url_rules(self, flask_app):
        self.app = flask_app

        flask_app.add_url_rule("/api/qa_tests/analysis", 'qa_tests_analysis', api_key_required(self.analyze_qa_tests), methods=['POST'])
        flask_app.add_url_rule("/api/qa_test_mappings/coverage/<path:pipeline_instance_id>", 'qa_test_mapping_coverage', api_key_required(self.get_qa_testmap_coverage), methods=['GET'])

    @json_response()
    def analyze_qa_tests(self):
        if 'X-Pipeline-Instance-Id' in request.headers:
            try:
                return self.qa_service.analyze_tests(int(request.headers['X-Pipeline-Instance-Id']), request.json)
            except Exception as exception:
                logger.exception(exception)
                
        raise HTTPException("Missing Pipeline Instance Id")

    @json_response()
    def get_qa_testmap_coverage(self, pipeline_instance_id):
        return self.qa_service.get_qa_testmap_coverage(pipeline_instance_id)
