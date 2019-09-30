from flask import send_from_directory, current_app

from rapid.lib import api_key_required, basic_auth


class FilesController(object):
    def __init__(self, flask_app):
        self.flask_app = flask_app

    def configure_routing(self):
        self.flask_app.add_url_rule('/get_file/<path:file_path>', 'get_file', basic_auth(self.get_file), methods=['GET'])

    def get_file(self, file_path):
        file_name = "/".join([self.flask_app.rapid_config.static_file_directory, file_path])
        return send_from_directory('/'.join(file_name.split('/')[0:-1]), file_name.split('/')[-1])
