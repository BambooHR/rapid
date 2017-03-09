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

import os

import sys
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def configure_data_layer(flask_app):
    global db
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = flask_app.rapid_config.db_connect_string
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    flask_app.db = db
    db.init_app(flask_app)

    from rapid.master.data.database.dal import setup_dals
    setup_dals(flask_app)


def run_db_upgrades(flask_app):
    with flask_app.app_context():
        from alembic import command

        config = _get_alembic_config(flask_app)
        command.upgrade(config, 'head')


def run_db_downgrade(flask_app, revision):
    with flask_app.app_context():
        from alembic import command

        config = _get_alembic_config(flask_app)
        command.downgrade(config, revision)


def create_revision(flask_app, message=None):
    with flask_app.app_context():
        from alembic import command

        config = _get_alembic_config(flask_app)
        command.revision(config, message, autogenerate=True)


def _get_alembic_config(flask_app):
    from alembic.config import Config
    return Config(config_args={'script_location': "{}/migrations".format(os.path.dirname(__file__)),
                               'sqlalchemy.url': flask_app.rapid_config.db_connect_string})

__all__ = ['configure_data_layer', 'db', 'create_revision']
