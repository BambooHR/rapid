from unittest import TestCase

from mock import patch, Mock

from rapid.client.action_instance_runner import ActionInstanceRunner


class TestActionInstanceRunner(TestCase):

    @patch('rapid.client.action_instance_runner.ClientCommunicator')
    @patch('rapid.client.action_instance_runner.Executor')
    @patch('rapid.client.action_instance_runner.WorkRequest')
    def test_run_action_instance_contract(self, wr, ex, ccom):
        mock_app = Mock()
        mock_config = Mock(master_uri='master',
                           quarantine_directory='quarantine',
                           verify_certs='verify',
                           workspace='work')
        mock_com = Mock()
        mock_wr = Mock()
        ccom.return_value = mock_com
        wr.return_value = mock_wr
        mock_com.get_work_request_by_action_instance_id.return_value = 'foobar'
        ai = ActionInstanceRunner(mock_config)
        ai.run_action_instance(mock_app, 111)

        ccom.assert_called_with('master', 'quarantine', mock_app, 'verify')
        mock_com.register.assert_called_with(mock_config)
        mock_com.get_work_request_by_action_instance_id.assert_called_with(111)

        wr.assert_called_with('foobar')
        ex.assert_called_with(mock_wr, 'master', workspace='work', quarantine='quarantine', verify_certs='verify', rapid_config=mock_config)
