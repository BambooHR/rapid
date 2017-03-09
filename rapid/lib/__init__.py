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
except:
    import json


from flask import request, current_app, Response
from functools import wraps

from rapid.lib.Exceptions import HttpException
from rapid.lib.Utils import RoutingUtil
from rapid.lib.framework.IOC import IOC


def setup_config_from_file(app, args):
    if app.rapid_config['_is'] == 'client':
        from ..client import ClientConfiguration
        app.rapid_config = ClientConfiguration.ClientConfiguration(args.config_file)
    elif app.rapid_config['_is'] == 'master':
        from ..master import MasterConfiguration
        app.rapid_config = MasterConfiguration.MasterConfiguration(args.config_file)
    IOC.register_global('rapid_config', app.rapid_config)


def api_key_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'X-Rapidci-Api-Key' in request.headers \
                and RoutingUtil.is_valid_request(request.headers['X-Rapidci-Api-Key'], current_app.rapid_config.api_key):
            return func(*args, **kwargs)
        else:
            return Response("Not authorized", status=401)
    return decorated_view


def json_response(exception_class=None, message=None):
    """
    :param exception_class: str
    :param message: str
    """
    def wrap(f):
        def wrapped_func(*args, **kwargs):
            try:
                response = f(*args, **kwargs)
                return Response(json.dumps(response), content_type="application/json")
            except Exception as exception_stuff:
                import traceback
                traceback.print_exc()
                if hasattr(exception_stuff, 'get_body'):
                    return exception_stuff
                else:
                    exception = exception_class(message) if exception_class is not None else Exception(exception_stuff.message)
                    response = Response(json.dumps(exception.to_dict())) if hasattr(exception, 'to_dict') else Response(json.dumps({"message": exception.__dict__}))
                    response.status_code = exception.status_code if hasattr(exception, 'status_code') else 500
                    response.content_type = 'application/json'
                    return response
        return wrapped_func
    return wrap
