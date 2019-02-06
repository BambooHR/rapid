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

import hmac
import logging

from hashlib import sha1

from github import Github
from github.GithubException import GithubException

from rapid.lib.features import Features
from rapid.lib.framework.injectable import Injectable

from rapid.lib.exceptions import HttpException
logger = logging.getLogger("rapid")


class GithubHelper(Injectable):
    __injectables__ = {'rapid_config': 'rapid_config'}
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"
    STATUS_FAILURE = "failure"

    def __init__(self, rapid_config):
        self.user = rapid_config.github_user
        self.password = rapid_config.github_pass

    def get_default_github(self, user=None, password=None):
        if user is None:
            user = self.user
        if password is None:
            password = self.password

        return Github(user, password)

    def record_status(self, request_json, commit_identifier, github=None):
        if Features.is_enabled(Features.TESTING) or not Features.is_enabled(Features.GITHUB_ALERTS):
            return 'Success!'

        if GithubHelper.is_valid_request_json(request_json):
            github = github if github is not None else self.get_default_github()
            repo = github.get_repo(request_json['pull_request_repo'])
            status = request_json['status']
            description = request_json['description']
            context = 'cihub-{}'.format(request_json['type'])
            log_uri = request_json['log_uri'] if 'log_uri' in request_json else ""
            try:
                if log_uri:
                    GithubHelper.set_commit_to_status(repo.get_commit(commit_identifier), status, description, context, target_url=log_uri)
                else:
                    GithubHelper.set_commit_to_status(repo.get_commit(commit_identifier), status, description, context)
                return "Success!"
            except GithubException as exception:
                if 'message' in exception.data and exception.data['message'] == 'Validation Failed':
                    logger.info("LOG_URI:  [{}]".format(log_uri))

                import traceback
                traceback.print_exc()
                raise exception

        raise HttpException("Invalid JSON")

    @staticmethod
    def set_commit_to_status(commit, status, description, context, target_url=None):
        if target_url is not None:
            commit.create_status(status, target_url=target_url, description=description, context=context)
        else:
            commit.create_status(status, description=description, context=context)

    @staticmethod
    def is_valid_request(signature, secret_key, data):
        if not signature or not secret_key or not data:
            return False

        if '=' in signature:
            signature = signature.split('=')[1]
        tmp_sig = GithubHelper.get_signature(secret_key, data)

        return signature == tmp_sig

    @staticmethod
    def get_signature(secret_key, data):
        return hmac.new(secret_key.encode('ascii', 'ignore'), data, sha1).hexdigest()

    @staticmethod
    def is_valid_request_json(request_json):
        assert 'pull_request_repo' in request_json, "Invalid JSON: missing pull_request_repo"
        assert 'status' in request_json, "Invalid JSON: missing status"
        assert 'type' in request_json, "Invalid JSON: missing type"
        assert request_json['status'] in [GithubHelper.STATUS_PENDING, GithubHelper.STATUS_SUCCESS, GithubHelper.STATUS_ERROR, GithubHelper.STATUS_FAILURE], "Invalid JSON: invalid status"

        return True

    @staticmethod
    def get_branch_from_ref(ref):
        return ref[len('refs/heads/'):] if ref is not None else None
