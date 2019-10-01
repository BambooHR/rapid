from ConfigParser import SafeConfigParser
from unittest import TestCase

from rapid.lib.configuration import ConfigurationDefaults, Configuration


class TestConfigurationDefaults(TestCase):
    def test_defaults_are_set_to_defaults(self):
        details = ConfigurationDefaults()
        self.assertEqual([None, str, ','], details.defaults)

    def test_defaults_set_right(self):
        defaults = ConfigurationDefaults('Testing', list, '')
        self.assertEqual(['Testing', list, ''], defaults.defaults)

    def test_defaults_work_with_configurations(self):
        config = TestingConfiguration()
        parser = SafeConfigParser()
        parser.add_section('test')
        parser.set('test', 'plain', 'Foo')
        parser.set('test', 'config_default', 'bar')

        config._set_values(parser)
        self.assertEqual('Foo', config.plain)
        self.assertEqual('bar', config.config_default)


class TestingConfiguration(Configuration):

    def __init__(self):
        self.plain = None
        self.config_default = None

        super(TestingConfiguration, self).__init__()

    @property
    def section_mapping(self):
        return {
            'test': {
                'plain': [None],
                'config_default': ConfigurationDefaults('working_default')
            }
        }
