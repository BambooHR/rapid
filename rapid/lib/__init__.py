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

try:
    import simplejson as json
except ImportError:
    import json

from functools import wraps
from flask import Response

from rapid.lib.exceptions import HttpException
from rapid.lib.utils import RoutingUtil
from rapid.lib.framework.ioc import IOC

db = None
Base = None

UWSGI = False
try:
    import uwsgi
    UWSGI = True
except ImportError:
    pass


def get_declarative_base():
    global Base  # pylint: disable=global-statement
    if Base is None:
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()
    return Base


def set_db(_db):
    global db  # pylint: disable=global-statement
    db = _db


def is_primary_worker():
    return uwsgi.worker_id() == 1 if UWSGI else not UWSGI


def get_db_session():
    session = db.session
    try:
        yield session
    finally:
        if session is not None:
            session.rollback()
            session.remove()
            session = None


def setup_config_from_file(app, args):
    if app.rapid_config['_is'] == 'client':
        from ..client import client_configuration
        app.rapid_config = client_configuration.ClientConfiguration(args.config_file)
    elif app.rapid_config['_is'] == 'master':
        from ..master import master_configuration
        app.rapid_config = master_configuration.MasterConfiguration(args.config_file)
    IOC.register_global('rapid_config', app.rapid_config)


def api_key_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'X-Rapidci-Api-Key' in get_current_request().headers \
                and RoutingUtil.is_valid_request(get_current_request().headers['X-Rapidci-Api-Key'], get_current_app().rapid_config.api_key):
            return func(*args, **kwargs)
        return Response("Not authorized", status=401)
    return decorated_view


def get_current_app():
    from flask import current_app
    return current_app


def get_current_request():
    from flask import request
    return request


def basic_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        config = get_current_app().rapid_config
        try:
            if config.basic_auth_user == get_current_request().authorization['username'] and config.basic_auth_pass == get_current_request().authorization['password']:
                return func(*args, **kwargs)
        except (KeyError, TypeError):
            pass
        return Response("Invalid Authorization", status=401)
    return wrapper


def json_response(exception_class=None, message=None):
    """
    :param exception_class: str
    :param message: str
    """
    def wrap(_f):
        def wrapped_json_response(*args, **kwargs):
            try:
                response = _f(*args, **kwargs)
                return Response(json.dumps(response), content_type="application/json")
            except Exception as exception_stuff:  # pylint: disable=broad-except
                import traceback
                traceback.print_exc()
                if hasattr(exception_stuff, 'get_body'):
                    return exception_stuff
                exception = exception_class(message) if exception_class is not None else Exception(str(exception_stuff))
                response = Response(json.dumps(exception.to_dict())) if hasattr(exception, 'to_dict') else Response(json.dumps({"message": exception.__dict__}))
                response.status_code = exception.status_code if hasattr(exception, 'status_code') else 500
                response.content_type = 'application/json'
                return response
        return wrapped_json_response
    return wrap


def setup_logging(flask_app):
    handler = logging.StreamHandler()
    if hasattr(flask_app.rapid_config, 'log_file') and flask_app.rapid_config.log_file:
        handler = logging.FileHandler(flask_app.rapid_config.log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # flask_app.logger.addHandler(handler)
    # flask_app.logger.setLevel(logging.INFO)

    logger = logging.getLogger('rapid')
    logger.addHandler(handler)
    logger.propagate = False  # Turn off double logging.
    logger.setLevel(logging.INFO)


def setup_status_route(flask_app):
    @flask_app.route('/status')
    def status():  # pylint: disable=unused-variable
        return 'Running'
