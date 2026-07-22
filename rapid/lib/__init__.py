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

from .framework.injectable import Injectable
from .framework.injector import Injector
from .framework.no_cache import NoCache

try:
    import simplejson as json
except ImportError:
    import json

from functools import wraps
from flask import Flask, Response

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
        IOC.register_global(client_configuration.ClientConfiguration, app.rapid_config)
    elif app.rapid_config['_is'] == 'master':
        from ..master import master_configuration
        app.rapid_config = master_configuration.MasterConfiguration(args.config_file)
        IOC.register_global(master_configuration.MasterConfiguration, app.rapid_config)

    from .configuration import Configuration

    IOC.register_global('rapid_config', app.rapid_config)
    IOC.register_global(Configuration, app.rapid_config)


def setup_ioc(flask_app):
    IOC.set_injector(Injector)
    IOC.set_injectable(Injectable)
    IOC.set_no_cacheable(NoCache)
    IOC.get_instance().is_cached = True

    IOC.register_global('flask_app', flask_app)
    IOC.register_global(Flask, flask_app)


def json_error_response(message, status=500):
    return Response(json.dumps({"message": message}), status=status, content_type='application/json')


def register_json_error_handlers(flask_app):
    """Ensure every unhandled error leaves the app as JSON rather than Flask's default HTML page."""
    from werkzeug.exceptions import HTTPException

    def handle_http_exception(error):
        # rapid HttpException subclasses already render a JSON body via get_body(); pass them through.
        if isinstance(error, HttpException):
            return error
        return json_error_response(error.description, error.code or 500)

    def handle_uncaught_exception(error):
        logging.getLogger('rapid').exception(error)
        return json_error_response("An internal error occurred.", 500)

    flask_app.register_error_handler(HTTPException, handle_http_exception)
    flask_app.register_error_handler(Exception, handle_uncaught_exception)


def api_key_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if 'X-Rapidci-Api-Key' in get_current_request().headers \
                and RoutingUtil.is_valid_request(get_current_request().headers['X-Rapidci-Api-Key'], get_current_app().rapid_config.api_key):
            return func(*args, **kwargs)
        return json_error_response("Not authorized", 401)
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
        return json_error_response("Invalid Authorization", 401)
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
                if isinstance(response, Response):
                    return response
                return Response(json.dumps(response), content_type="application/json")
            except Exception as exception_stuff:  # pylint: disable=broad-except
                if isinstance(exception_stuff, HttpException):
                    return exception_stuff  # already renders a JSON body via get_body()
                if exception_class is not None:
                    return json_error_response(message, 500)
                description = getattr(exception_stuff, 'description', None) or str(exception_stuff)
                status = getattr(exception_stuff, 'code', None) or getattr(exception_stuff, 'status_code', None) or 500
                return json_error_response(description, status)
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
        return Response(json.dumps({"status": "Running"}), content_type='application/json')
