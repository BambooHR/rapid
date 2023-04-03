from unittest import TestCase

from mock import Mock, patch, call

from rapid.lib.constants import StatusConstants
from rapid.lib.exceptions import ECSLimitReached, QueueHandlerShouldSleep, ECSConnectionError
from rapid.workflow.queue_handlers.handlers.ecs_queue_handler import ECSQueueHandler
from rapid.lib.queue_handler_constants import QueueHandlerConstants


class TestECSQueueHandler(TestCase):
    def setUp(self):
        self.config = Mock()
        self.action_instance_service = Mock()
        self.handler = ECSQueueHandler(self.config, self.action_instance_service)

    def test_ecs_queue_handler_auto_registers(self):
        self.assertTrue(ECSQueueHandler in QueueHandlerConstants.queue_handler_classes)

    def test_container_identifier(self):
        self.assertEqual('ecs', self.handler.container_identifier)

    def test_get_task_definition_key_no_key(self):
        self.assertEqual(None, self.handler._get_task_definition_key(Mock(), ''))

    def test_get_task_definition_key_no_children(self):
        testing = {}
        self.assertEqual({}, self.handler._get_task_definition_key(testing, 'foo:dict'))
        self.assertEqual({}, testing['foo'])

    def test_get_task_definition_key_with_children(self):
        testing = {}
        self.assertEqual([], self.handler._get_task_definition_key(testing, 'foo:dict.bar:dict.trial:list'))
        self.assertEqual([], testing['foo']['bar']['trial'])

    def test_get_task_definition_key_with_bad_key(self):
        testing = {}
        self.assertEqual(None, self.handler._get_task_definition_key(testing, 'foo.bar.trial'))
        self.assertEqual({}, testing)

    def test_get_task_definition_key_with_existing_data(self):
        testing = {'foo': {'bar': [1, 2, 3]}}
        self.assertEqual([1, 2, 3], self.handler._get_task_definition_key(testing, 'foo:dict.bar:list'))

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.datetime')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_task_definition')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._set_task_status')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._run_task')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_ecs_client')
    def test_process_work_request(self, client, run_task, set_task, get_task, mock_datetime):
        mock_datetime.datetime.utcnow.return_value = 'foo'
        mock_work_request = Mock(action_instance_id=1, grain='foo')
        task_def = {'foo': 'bar', 'taskDefinition': 'fake'}
        run_task.return_value = (-101010, '--ecs--foo')
        get_task.return_value = task_def
        self.handler.process_work_request(mock_work_request, [])
        get_task.assert_called_with(mock_work_request)
        run_task.assert_called_with(task_def)
        set_task.assert_has_calls([call(1, -101010, '--ecs--foo', start_date='foo')])

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_overridden_task_definition')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._inject_work_request_parameters')
    def test_get_task_definition_call_contract(self, inject_work, get_overridden):
        mock = Mock()
        mock_request = Mock()
        get_overridden.return_value = mock
        self.handler._get_task_definition(mock_request)
        get_overridden.assert_called_with(mock_request.configuration)
        inject_work.assert_called_with(mock, mock_request)

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.json')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.logger')
    def test_get_overridden_task_definition(self, logger, mock_json):
        mock_json.loads.return_value = {'key': 'value'}
        self.handler._ecs_configuration = Mock(default_task_definition={'key': 'bogus'})
        
        self.assertEqual({'key': 'value'}, self.handler._get_overridden_task_definition('testing'))
        mock_json.loads.assert_called_with('testing')

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_task_definition_key')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_grain_type_split')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_substituted_value')
    def test_inject_work_request_parameters_contract(self, get_sub_value, get_grain_split, task_definition_key):
        task_definition = {}
        mock_check = []
        work_request = Mock(action_instance_id=1, workflow_instance_id=2, pipeline_instance_id=3, grain='foo')
        task_definition_key.return_value = mock_check
        get_grain_split.return_value = ('foo', "bar\n")
        get_sub_value.return_value = 'sub_value'

        self.handler._inject_work_request_parameters(task_definition, work_request)
        self.assertEqual([{'name': 'bar\n', 'environment': [{'name': 'action_instance_id', 'value': '1'},
                                                            {'name': 'workflow_instance_id', 'value': '2'},
                                                            {'name': 'pipeline_instance_id', 'value': '3'}]}], mock_check)
        task_definition_key.assert_called_with(task_definition, 'overrides:dict.containerOverrides:list')
        get_grain_split.assert_called_with('foo')
        get_sub_value.assert_called_with(work_request, 'bar')
        self.assertEqual('sub_value', task_definition['taskDefinition'])

    def test_set_task_status_contract(self):
        self.handler._set_task_status(1, 12345, 'testing')
        self.action_instance_service.edit_action_instance.assert_called_with(1, {'status_id': 12345, 'assigned_to': '--ecs--testing'})

    def test_set_task_status_default_assigned_to(self):
        self.handler._set_task_status(1, 12345, '')
        self.action_instance_service.edit_action_instance.assert_called_with(1, {'status_id': 12345, 'assigned_to': '--ecs--'})

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_ecs_client')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.logger')
    def test_run_task_failed_when_ecs_run_task_fails_with_failures(self, logger, ecs_client):
        mock = Mock()
        ecs_client.return_value = mock
        mock.run_task.return_value = {'failures': [{}], 'tasks': [1]}
        (status_id, assigned_to) = self.handler._run_task({'some': 'thing'})

        mock.run_task.assert_called_with(some='thing')
        self.assertEqual(StatusConstants.FAILED, status_id)
        self.assertEqual('', assigned_to)

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_ecs_client')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.logger')
    def test_run_task_reset_when_ecs_run_task_no_failures_with_empty_tasks(self, logger, ecs_client):
        mock = Mock()
        ecs_client.return_value = mock
        mock.run_task.return_value = {'failures': [], 'tasks': []}
        (status_id, assigned_to) = self.handler._run_task({'some': 'thing'})

        self.assertEqual(1, logger.error.call_count)
        self.assertEqual(StatusConstants.READY, status_id)
        self.assertEqual('', assigned_to)

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_ecs_client')
    def test_run_task_failed_when_ecs_run_task_passes_works_right(self, ecs_client):
        mock = Mock()
        ecs_client.return_value = mock
        mock.run_task.return_value = {'failures': [], 'tasks': [{'taskArn': '12345'}]}
        (status_id, assigned_to) = self.handler._run_task({'some': 'thing'})

        self.assertEqual(StatusConstants.INPROGRESS, status_id)
        self.assertEqual('--ecs--12345', assigned_to)

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.re')
    def test_get_substituted_value_no_substring(self, mock_re):
        self.assertEqual('floobar', self.handler._get_substituted_value(Mock(), 'floobar'))
        mock_re.findall.assert_not_called()

    def test_get_substituted_value_incomplete_wrapping(self):
        self.assertEqual('{floobar', self.handler._get_substituted_value(Mock(), '{floobar'))

    def test_get_substituted_value_with_no_replacement_value_returns(self):
        mock = Mock()
        del mock.floobar
        self.assertEqual('{floobar}', self.handler._get_substituted_value(mock, '{floobar}'))

    def test_get_substituted_value_substitutes_value(self):
        self.assertEqual('worky!', self.handler._get_substituted_value(Mock(floobar='worky!'), '{floobar}'))

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._load_aws_config')
    def test_get_ecs_client_contract(self, load_config):
        load_config.return_value = 'worky!'
        self.assertEqual('worky!', self.handler._get_ecs_client())
        load_config.assert_called_with()

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._load_aws_config')
    def test_get_ecs_client_caching(self, load_config):
        load_config.return_value = 'worky!'
        self.handler._ecs_client = 'OHYEAH!'
        self.assertEqual('OHYEAH!', self.handler._get_ecs_client())
        load_config.assert_not_called()

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSConfiguration')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.boto3')
    def test_load_aws_config(self, boto3, config):
        config.return_value = Mock(aws_credentials={'some': 'BOO!'})
        self.handler._load_aws_config()
        boto3.client.assert_called_with('ecs', some='BOO!')

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_ecs_client')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_task_definition')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._set_task_status')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._run_task')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.logger')
    def test_process_work_handles_sleep_exception(self, logger, run_task, set_task_status, task_definition, ecs_client):
        task_definition.return_value = {'taskDefinition': Mock()}
        run_task.side_effect = ECSLimitReached("Foobar")

        with self.assertRaises(QueueHandlerShouldSleep):
            self.handler.process_work_request(Mock(action_instance_id=1), [])

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_ecs_client')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.logger')
    def test_run_task_handles_limit_failures_right(self, logger, client):
        mock_client = Mock()
        mock_client.run_task.return_value = {'failures': [{'reason': "You've reached the limit on the number of tasks you can run concurrently"}]}

        client.return_value = mock_client

        with self.assertRaises(ECSLimitReached) as exception:
            self.handler._run_task({})

        self.assertEqual("You've reached the limit on the number of tasks you can run concurrently", f"{exception.exception}")

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_ecs_client')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.logger')
    def test_run_task_handles_connect_failures_right(self, logger, client):
        mock_client = Mock()
        mock_client.run_task.return_value = {'failures': [{'reason': "Error retrieving security group information: com.amazonaws.SdkClientException: Unable to execute HTTP request: Connect to ec2.us-east-1.amazonaws.com:443 [ec2.us-east-1.amazonaws.com/54.239.31.174] failed: connect timed out"}]}

        client.return_value = mock_client

        with self.assertRaises(ECSConnectionError):
            self.handler._run_task({})

    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.ECSQueueHandler._get_ecs_client')
    @patch('rapid.workflow.queue_handlers.handlers.ecs_queue_handler.logger')
    def test_run_task_fails_if_reason_not_given(self, logger, client):
        mock_client = Mock()
        mock_client.run_task.return_value = {'failures': [{}]}

        client.return_value = mock_client

        (status_id, assigned_to) = self.handler._run_task({})
        self.assertEqual(StatusConstants.FAILED, status_id)
