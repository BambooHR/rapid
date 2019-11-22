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

try:
    import simplejson as json
except ImportError:
    import json


from werkzeug.exceptions import HTTPException


class HttpException(HTTPException):
    code = 400
    headers = {'Content-Type': 'application/json'}

    def __init__(self, description=None, code=400):
        super(HttpException, self).__init__(description)
        self.code = code

    def get_headers(self, environ=None):
        return self.headers

    def get_body(self, environ=None):
        return json.dumps({"message": self.description})


class ThresholdException(BaseException):
    pass


class ResultsFileNotFoundException(BaseException):
    pass


class ResultsFileNotParsedException(BaseException):
    pass


class UnAuthorizedException(HttpException):
    def __init__(self, message):
        super(UnAuthorizedException, self).__init__(description=message)
        self.code = 401
        self.headers['WWW-Authenticate'] = 'Basic realm="Login Required"'


class VcsNotFoundException(HttpException):
    def __init__(self, message):
        super(VcsNotFoundException, self).__init__(description=message)
        self.code = 401


class DatabaseException(HttpException):
    pass


class InvalidObjectException(HttpException):
    pass


class InvalidReportException(HttpException):
    pass


class ECSLimitReached(Exception):
    pass


class ECSConnectionError(Exception):
    pass


class QueueHandlerShouldSleep(Exception):
    pass
