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

import argparse
import logging

from .configuration_generator import ConfigurationGenerator

parser = argparse.ArgumentParser(description='Rapid Framework client main control')
parser.add_argument('-f', '--config', dest='config_file', help="config file path")
parser.add_argument('-p', '--port', dest='port', help='Port for the master to listen on')
parser.add_argument('-m', '--master', dest='mode_master', help='Master mode is default', action='store_true')
parser.add_argument('-c', '--client', dest='mode_client', help='Client mode', action='store_true')
parser.add_argument('-l', '--logging', dest='mode_logging', help='Logging mode', action='store_true')
parser.add_argument('-d', '--log_dir', dest='log_dir', help='Logging directory')
parser.add_argument('-q', '--qa_dir', dest="qa_dir", help="QA Dir")
parser.add_argument('-w', '--waitress', dest='waitress', action='store_true', help='Run under waitress')
parser.add_argument('-r', '--run', dest='run', help='Run action_instance_id')
parser.add_argument('-u', '--upgrade', dest='upgrade', action='store_true', help="Upgrade to master's version")
parser.add_argument('--static_file_dir', dest='static_file_dir', help='Static File directory, default is current')
parser.add_argument('--static_basic_auth', dest='basic_auth', help="Basic Auth for static file directory")
parser.add_argument('--downgrade', dest='db_downgrade', help="Downgrade db for alembic")
parser.add_argument('--create_db', action='store_true', dest='createdb', help="Create initial db")
parser.add_argument('--create_migration', dest='migrate', help="Create Migration for alembic")
parser.add_argument('--generate-config', dest='generate_config', help='Generate a default configuration', choices=['master', 'client'])
args = parser.parse_args()

if args.mode_client or args.run or args.upgrade:
    from .client import app, configure_application
elif args.mode_logging:
    from .log_server import app, configure_application
elif args.qa_dir:
    from .testmapper import process_directory
    process_directory('', args.qa_dir, True)
    import sys
    sys.exit(0)
elif args.generate_config:
    import sys
    ConfigurationGenerator().generate(args.generate_config, args.config_file)
    sys.exit(0)
else:
    from .master import app, configure_application

logger = logging.getLogger("rapid")


def setup():
    logger.info("Setting up the application.")
    configure_application(app, args)


if not args.migrate:
    setup()


def main():
    if args.createdb:
        with app.app_context():
            app.db.create_all()  # pylint: disable=no-member
    if args.migrate:
        from .master import create_migration_script
        configure_application(app, args, manual_db_upgrade=True)
        create_migration_script(app, args.migrate)
    elif args.db_downgrade:
        print("Downgraded.")
    elif args.waitress:
        try:
            from waitress import serve
            serve(app, port=(int(args.port or app.rapid_config.port)))  # pylint: disable=no-member
        except ImportError:
            print("Failed to start up the server.")
    elif args.run:
        from rapid.client import run_action_instance
        run_action_instance(args.run)
    elif args.upgrade:
        from rapid.client import upgrade_rapid
        upgrade_rapid()
    else:
        app.run('0.0.0.0', port=int(args.port or app.rapid_config.port))  # pylint: disable=no-member


if __name__ == '__main__':
    main()



