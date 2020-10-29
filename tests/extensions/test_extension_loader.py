from unittest.case import TestCase
from unittest.mock import MagicMock, patch, call

from rapid.extensions.extension_loader import ExtensionLoader


class TestExtensionLoader(TestCase):

    def setUp(self) -> None:
        self.mock_config = MagicMock()
        self.loader = ExtensionLoader(self.mock_config)

    @patch('rapid.extensions.extension_loader.importlib')
    def test_load_extensions_none_configuration(self, mock_lib):
        self.mock_config.extensions = None
        self.loader.load_extensions(None)
        mock_lib.import_module.assert_not_called()

    @patch('rapid.extensions.extension_loader.importlib')
    def test_load_extensions_empty_configuration(self, mock_lib):
        self.mock_config.extensions = []
        self.loader.load_extensions(None)
        mock_lib.import_module.assert_not_called()

    @patch('rapid.extensions.extension_loader.importlib')
    @patch('rapid.extensions.extension_loader.logger')
    def test_load_extensions_invalid_extensions(self, logger, mock_lib):
        self.mock_config.extensions = ['foobar-bad-boy']
        mock = MagicMock()
        del mock.setup_rapid
        mock_lib.import_module.return_value = mock

        self.loader.load_extensions(None)
        logger.info.assert_called_with("The extension 'foobar-bad-boy' does not have a 'setup_rapid' method.")

    @patch('rapid.extensions.extension_loader.importlib')
    @patch('rapid.extensions.extension_loader.logger')
    def test_load_extensions_valid_extensions(self, logger, mock_lib):
        self.mock_config.extensions = ['foobar-bad-boy']
        mock = MagicMock()
        mock_flask = MagicMock()
        mock_lib.import_module.return_value = mock

        self.loader.load_extensions(mock_flask)
        mock.setup_rapid.assert_called_with(mock_flask, self.mock_config)
        logger.info.assert_called_with('The extension "foobar-bad-boy" was loaded.')

    @patch('rapid.extensions.extension_loader.importlib')
    @patch('rapid.extensions.extension_loader.logger')
    def test_load_extensions_module_import_failure(self, logger, mock_lib):
        self.mock_config.extensions = ['bogus', 'failed-import']
        mock_lib.import_module.side_effect = [ModuleNotFoundError('This should fail'), ImportError('This should fail also')]

        self.loader.load_extensions(None)
        logger.info.assert_has_calls([call('The extension named "bogus" was not loaded.'), call('The extension named "failed-import" was not loaded.')])
