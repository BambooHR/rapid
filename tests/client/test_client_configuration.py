from configparser import ConfigParser
from unittest.case import TestCase

from rapid.client.client_configuration import ClientConfiguration


class TestClientConfiguration(TestCase):

    def test_os_path_override_setting(self):
        parser = ConfigParser()
        parser.add_section('client')
        parser.set('client', 'os_path_override', "f")
        client_config = ClientConfiguration()
        client_config._set_values(parser)

        self.assertEqual('f', client_config.os_path_override)

    def test_os_path_override_default(self):
        parser = ConfigParser()
        parser.add_section('client')
        client_config = ClientConfiguration()
        client_config._set_values(parser)

        self.assertEqual(None, client_config.os_path_override)
