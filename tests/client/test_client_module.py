from unittest import TestCase

from mock import patch, Mock

from rapid.client import configure_application


class TestClientModule(TestCase):
    @patch('rapid.client.setup_status_route')
    @patch('rapid.client.setup_config_from_file')
    @patch('rapid.client.setup_logger')
    @patch('rapid.client.load_parsers')
    @patch('rapid.client.register_controllers')
    @patch('rapid.client.is_primary_worker')
    @patch('rapid.client.setup_client_register_thread')
    @patch('rapid.client.clean_workspace')
    def test_configure_application_register_thread(self, cw, scrt, ipw, rc, lp, sl, scff, ssr):
        ipw.return_value = True
        mock_app = Mock()
        args = Mock(run=False)
        configure_application(mock_app, args)
        cw.assert_called_with()
        scrt.assert_called_with()
        ipw.assert_called_with()
        rc.assert_called_with(mock_app)
        lp.assert_called_with()
        sl.assert_called_with(mock_app)
        scff.assert_called_with(mock_app, args)
        ssr.assert_called_with(mock_app)

    @patch('rapid.client.setup_status_route')
    @patch('rapid.client.setup_config_from_file')
    @patch('rapid.client.setup_logger')
    @patch('rapid.client.load_parsers')
    @patch('rapid.client.register_controllers')
    @patch('rapid.client.is_primary_worker')
    @patch('rapid.client.setup_client_register_thread')
    @patch('rapid.client.clean_workspace')
    def test_configure_application_does_not_register_when_not_primary(self, cw, scrt, ipw, rc, lp, sl, scff, ssr):
        ipw.return_value = False
        mock_app = Mock()
        args = Mock(run=False)
        configure_application(mock_app, args)
        self.assertEqual(0, cw.call_count)
        self.assertEqual(0, scrt.call_count)

    @patch('rapid.client.setup_status_route')
    @patch('rapid.client.setup_config_from_file')
    @patch('rapid.client.setup_logger')
    @patch('rapid.client.load_parsers')
    @patch('rapid.client.register_controllers')
    @patch('rapid.client.is_primary_worker')
    @patch('rapid.client.setup_client_register_thread')
    @patch('rapid.client.clean_workspace')
    def test_configure_application_does_not_register_when_runs_an_action_instance(self, cw, scrt, ipw, rc, lp, sl, scff, ssr):
        ipw.return_value = True
        mock_app = Mock()
        args = Mock(run=True)
        configure_application(mock_app, args)
        self.assertEqual(0, cw.call_count)
        self.assertEqual(0, scrt.call_count)
