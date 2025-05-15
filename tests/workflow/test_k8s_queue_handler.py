from mock.mock import Mock, patch, call
import urllib3

from rapid.lib.constants import StatusConstants
from rapid.lib.exceptions import QueueHandlerShouldSleep, K8SServiceUnavailable, K8SConnectionError
from rapid.lib.queue_handler_constants import QueueHandlerConstants
from rapid.workflow.queue_handlers.handlers.k8s_queue_handler import K8SQueueHandler
from tests.framework.unit_test import UnitTest


class TestK8SQueueHandler(UnitTest):
    def setUp(self):
        self.setup_ioc()
        self.config = Mock()
        self.action_instance_service = Mock()
        self.handler = K8SQueueHandler(self.config, self.action_instance_service)

    def tearDown(self):
        self.teardown_ioc()
        
    def test_k8s_queue_handler_auto_registers(self):
        """Test that K8SQueueHandler automatically registers with QueueHandlerConstants."""
        self.assertTrue(K8SQueueHandler in QueueHandlerConstants.queue_handler_classes)
        
    def test_container_identifier(self):
        """Test that container_identifier property returns 'k8s'."""
        self.assertEqual('k8s', self.handler.container_identifier)
        
    def test_assigned_to_prefix(self):
        """Test that assigned_to_prefix property returns the correct prefix."""
        self.assertEqual('--k8s--', self.handler.assigned_to_prefix)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    def test_core_api_v1_loads_client_config(self, mock_load_client):
        """Test that core_api_v1 property calls _load_k8s_client."""

        # Access the property to trigger the loading
        with patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.client'):
            _ = self.handler.core_api_v1
            
        # Verify _load_k8s_client was called
        mock_load_client.assert_called()
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.client')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    def test_core_api_v1_creates_api_instance(self, mock_config, mock_client):
        """Test that core_api_v1 property creates a CoreV1Api instance."""
        # Setup mock
        mock_core_api = Mock()
        mock_client.CoreV1Api.return_value = mock_core_api
        
        # Access the property
        result = self.handler.core_api_v1
        
        # Verify CoreV1Api was created
        mock_client.CoreV1Api.assert_called()
        self.assertEqual(mock_core_api, result)
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.client')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    def test_core_api_v1_caches_instance(self, mock_config, mock_client):
        """Test that core_api_v1 property caches the CoreV1Api instance."""
        # Setup mock
        mock_core_api = Mock()
        mock_client.CoreV1Api.return_value = mock_core_api
        
        # First call to create and cache the instance
        first_result = self.handler.core_api_v1
        
        # Reset the mock to verify it's not called again
        mock_client.CoreV1Api.reset_mock()
        
        # Second call should use the cached instance
        second_result = self.handler.core_api_v1
        
        # Verify CoreV1Api was not created again
        mock_client.CoreV1Api.assert_not_called()
        self.assertEqual(first_result, second_result)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    def test_batch_api_v1_loads_client_config(self, mock_load_client):
        """Test that batch_api_v1 property calls _load_k8s_client."""
        # Access the property to trigger the loading
        with patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.client'):
            _ = self.handler.batch_api_v1
            
        # Verify _load_k8s_client was called
        mock_load_client.assert_called()
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.client')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    def test_batch_api_v1_creates_api_instance(self, mock_config,mock_client):
        """Test that batch_api_v1 property creates a BatchV1Api instance."""
        # Setup mock
        mock_batch_api = Mock()
        mock_client.BatchV1Api.return_value = mock_batch_api
        
        # Access the property
        result = self.handler.batch_api_v1
        
        # Verify BatchV1Api was created
        mock_client.BatchV1Api.assert_called()
        self.assertEqual(mock_batch_api, result)
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.client')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    def test_batch_api_v1_caches_instance(self, mock_config, mock_client):
        """Test that batch_api_v1 property caches the BatchV1Api instance."""
        # Setup mock
        mock_batch_api = Mock()
        mock_client.BatchV1Api.return_value = mock_batch_api
        
        # First call to create and cache the instance
        first_result = self.handler.batch_api_v1
        
        # Reset the mock to verify it's not called again
        mock_client.BatchV1Api.reset_mock()
        
        # Second call should use the cached instance
        second_result = self.handler.batch_api_v1
        
        # Verify BatchV1Api was not created again
        mock_client.BatchV1Api.assert_not_called()
        self.assertEqual(first_result, second_result)
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    def test_load_k8s_client_first_call(self, mock_config):
        """Test that _load_k8s_client loads the configuration on first call."""

        # Initially _is_loaded should be False
        self.assertFalse(self.handler._is_loaded)
        
        # Call the method
        self.handler._load_k8s_client()
        
        # Verify the configuration was loaded
        mock_config.load_incluster_config.assert_called()
        
        # Verify _is_loaded was set to True
        self.assertTrue(self.handler._is_loaded)
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    def test_load_k8s_client_subsequent_calls(self, mock_config):
        """Test that _load_k8s_client does not load the configuration on subsequent calls."""
        # Create a new handler instance without the patched _load_k8s_client

        # First call to load the configuration
        self.handler._load_k8s_client()
        
        # Reset the mock
        mock_config.load_incluster_config.reset_mock()
        
        # Second call should not load the configuration again
        self.handler._load_k8s_client()
        
        # Verify the configuration was not loaded again
        mock_config.load_incluster_config.assert_not_called()
        
        # Verify _is_loaded is still True
        self.assertTrue(self.handler._is_loaded)
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.yaml')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.open', create=True)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_grain_type_split.__name__)
    def test_get_job_definition_success(self, mock_grain_split, mock_open, mock_yaml):
        """
        Test that _get_job_definition method loads a job definition from a YAML file
        based on the grain name and returns it.
        """
        # Setup mocks
        mock_grain_split.return_value = ('k8s', 'test-job')
        self.config.k8s_config_dir = '/path/to/k8s/configs'
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        expected_job = {'apiVersion': 'batch/v1', 'kind': 'Job'}
        mock_yaml.safe_load.return_value = expected_job
        
        # Call the method
        work_request = Mock(grain='k8s://test-job')
        result = self.handler._get_job_definition(work_request)
        
        # Verify the results
        mock_grain_split.assert_called_with('k8s://test-job')
        mock_open.assert_called_with('/path/to/k8s/configs/test-job.yaml', 'r')
        mock_yaml.safe_load.assert_called_with(mock_file)
        self.assertEqual(expected_job, result)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_grain_type_split.__name__)
    def test_get_job_definition_file_not_found(self, mock_grain_split):
        """
        Test that _get_job_definition method raises FileNotFoundError when the job definition file
        does not exist.
        """
        # Setup mocks
        mock_grain_split.return_value = ('k8s', 'non-existent-job')
        self.config.k8s_config_dir = '/path/to/k8s/configs'
        
        # Call the method and verify it raises FileNotFoundError
        work_request = Mock(grain='k8s://non-existent-job')
        with patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.open', create=True) as mock_open:
            mock_open.side_effect = FileNotFoundError()
            with self.assertRaises(FileNotFoundError):
                self.handler._get_job_definition(work_request)
        
        mock_grain_split.assert_called_with('k8s://non-existent-job')
        
    def test_job_name_combines_grain_name_and_ids(self):
        """Test that _job_name combines grain name, pipeline instance ID, and action instance ID."""
        # Setup test data
        grain_name = 'test-job'
        pipeline_instance_id = 123
        action_instance_id = 456
        
        # Expected format: grain_name-pipeline_id.action_id
        expected_job_name = 'test-job-123.456'
        
        # Call the method
        result = self.handler._job_name(grain_name, pipeline_instance_id, action_instance_id)
        
        # Verify the result matches the expected format
        self.assertEqual(expected_job_name, result)
        
    def test_job_name_truncates_long_grain_names(self):
        """Test that _job_name truncates grain names to respect the 63-character Kubernetes limit."""
        # Create a grain name that would result in a job name longer than 63 characters
        long_grain_name = 'very-long-grain-name-that-exceeds-kubernetes-63-character-limit-for-job-names'
        pipeline_instance_id = 123456
        action_instance_id = 789012
        
        # Call the method
        result = self.handler._job_name(long_grain_name, pipeline_instance_id, action_instance_id)
        
        # Verify the result is no longer than 63 characters
        self.assertLessEqual(len(result), 63)
        
    def test_job_name_preserves_ids_when_truncating(self):
        """Test that _job_name preserves the IDs when truncating long grain names."""
        # Create a grain name that would result in a job name longer than 63 characters
        long_grain_name = 'very-long-grain-name-that-exceeds-kubernetes-63-character-limit-for-job-names'
        pipeline_instance_id = 123456
        action_instance_id = 789012
        
        # Calculate the expected truncated job name
        id_part = f'-{pipeline_instance_id}.{action_instance_id}'
        max_grain_length = 63 - len(id_part)
        expected_job_name = f'{long_grain_name[:max_grain_length]}{id_part}'
        
        # Call the method
        result = self.handler._job_name(long_grain_name, pipeline_instance_id, action_instance_id)
        
        # Verify the result matches the expected truncated format
        self.assertEqual(expected_job_name, result)
        
        # Verify the ID part is preserved at the end
        self.assertTrue(result.endswith(id_part))
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch.object(K8SQueueHandler, K8SQueueHandler._run_task.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_run_task_success(self, mock_set_task_status, mock_run_task, mock_datetime, mock_load_client):
        """Test that _run_task method successfully creates a Kubernetes job."""
        # Setup mocks
        mock_work_request = Mock(
            action_instance_id=123,
            pipeline_instance_id=456,
            environment={'ENV_VAR1': 'value1', 'ENV_VAR2': 'value2'}
        )
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Create a new batch_api_v1 mock
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Call the method
        self.handler._run_task(mock_work_request, mock_job)
        
        # Verify job name was generated and set
        mock_run_task.assert_called_with(mock_work_request, mock_job)
        self.assertEqual('test-job', mock_job['metadata']['name'])
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_run_task_adds_environment_variables(self, mock_set_task_status, mock_job_name, mock_datetime, mock_load_client):
        """Test that _run_task method adds environment variables to the container."""
        # Setup mocks
        mock_work_request = Mock(
            action_instance_id=123,
            pipeline_instance_id=456,
            environment={'ENV_VAR1': 'value1', 'ENV_VAR2': 'value2'}
        )
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Setup get_default_environment mock
        self.handler.get_default_environment = Mock(return_value=[{'name': 'DEFAULT_ENV', 'value': 'default_value'}])
        
        # Create a new batch_api_v1 mock
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Call the method
        self.handler._run_task(mock_work_request, mock_job)
        
        # Verify environment variables were added to the container
        container_env = mock_job['spec']['template']['spec']['containers'][0]['env']
        self.assertIsNotNone(container_env)
        self.assertIn({'name': 'DEFAULT_ENV', 'value': 'default_value'}, container_env)
        self.assertIn({'name': 'ENV_VAR1', 'value': 'value1'}, container_env)
        self.assertIn({'name': 'ENV_VAR2', 'value': 'value2'}, container_env)
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    def test_run_task_creates_namespaced_job(self, mock_config, mock_set_task_status, mock_job_name, mock_datetime):
        """Test that _run_task method creates a namespaced job."""
        # Setup mocks
        mock_work_request = Mock(
            action_instance_id=123,
            pipeline_instance_id=456,
            environment={}
        )
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Setup get_default_environment mock
        self.handler.get_default_environment = Mock(return_value=[])
        
        # Create a new batch_api_v1 mock
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Call the method
        self.handler._run_task(mock_work_request, mock_job)
        
        # Verify the job was created
        batch_api_mock.create_namespaced_job.assert_called_with(
            namespace='cihub', body=mock_job
        )
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_run_task_sets_task_status(self, mock_set_task_status, mock_job_name, mock_datetime, mock_load_client):
        """Test that _run_task method sets the task status to INPROGRESS."""
        # Setup mocks
        mock_work_request = Mock(
            action_instance_id=123,
            pipeline_instance_id=456,
            environment={}
        )
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Setup get_default_environment mock
        self.handler.get_default_environment = Mock(return_value=[])
        
        # Create a new batch_api_v1 mock
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Call the method
        self.handler._run_task(mock_work_request, mock_job)
        
        # Verify the task status was set to INPROGRESS
        mock_set_task_status.assert_called_with(
            123, 
            StatusConstants.INPROGRESS, 
            assigned_to='--k8s--test-job-456.123',
            start_date='mock_datetime'
        )
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.json')
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_run_task_sets_status_to_failed_for_api_exception_404(self, mock_set_task_status, mock_job_name, mock_json, mock_datetime, mock_load_client):
        """Test that _run_task sets task status to FAILED when ApiException with status 404 occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123, pipeline_instance_id=456, environment={})
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Create a new batch_api_v1 mock
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Setup ApiException mock with status 404
        from kubernetes.client.rest import ApiException
        api_exception = ApiException(status=404, reason="Not Found")
        api_exception.body = '{"message": "Not found"}'
        mock_json.loads.return_value = {'message': 'Not found'}
        batch_api_mock.create_namespaced_job.side_effect = api_exception
        
        # Call the method
        self.handler._run_task(mock_work_request, mock_job)
        
        # Verify the task status was set to FAILED
        mock_set_task_status.assert_called_with(
            123, 
            StatusConstants.FAILED,
            start_date='mock_datetime',
            end_date='mock_datetime'
        )
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.json')
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.logger')
    def test_run_task_sets_status_to_failed_for_api_exception_422(self, mock_logger, mock_config, mock_set_task_status, mock_job_name, mock_json, mock_datetime):
        """Test that _run_task sets task status to FAILED when ApiException with status 422 occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123, pipeline_instance_id=456, environment={})
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Create a new batch_api_v1 mock with ApiException
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Setup ApiException mock with status 422
        from kubernetes.client.rest import ApiException
        api_exception = ApiException(status=422, reason="Unprocessable Entity")
        api_exception.body = '{"message": "Validation failed"}'
        mock_json.loads.return_value = {'message': 'Validation failed'}
        batch_api_mock.create_namespaced_job.side_effect = api_exception
        
        # Call the method
        self.handler._run_task(mock_work_request, mock_job)
        
        # Verify the task status was set to FAILED
        mock_set_task_status.assert_called_with(
            123, 
            StatusConstants.FAILED,
            start_date='mock_datetime',
            end_date='mock_datetime'
        )
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.logger')
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    def test_run_task_logs_error_for_key_error(self, mock_config, mock_set_task_status, mock_job_name, mock_logger, mock_datetime):
        """Test that _run_task logs an error when a KeyError occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123, pipeline_instance_id=456)
        mock_job = {'metadata': {}}  # Missing required keys
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Make _job_name raise a KeyError when called
        mock_job_name.side_effect = KeyError('metadata')
        
        # Call the method
        self.handler._run_task(mock_work_request, mock_job)
        
        # Verify the error was logged
        mock_logger.error.assert_called()
        
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.logger')
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.config')
    def test_run_task_sets_status_to_failed_for_key_error(self, mock_config, mock_set_task_status, mock_job_name, mock_logger, mock_datetime):
        """Test that _run_task sets task status to FAILED when a KeyError occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123, pipeline_instance_id=456)
        mock_job = {'metadata': {}}  # Missing required keys
        mock_job_name.return_value = 'test-job-456.123'
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Make _job_name raise a KeyError when called
        mock_job_name.side_effect = KeyError('metadata')
        
        # Call the method
        self.handler._run_task(mock_work_request, mock_job)
        
        # Verify the task status was set to FAILED
        mock_set_task_status.assert_called_with(
            123, 
            StatusConstants.FAILED,
            start_date='mock_datetime',
            end_date='mock_datetime'
        )
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    def test_run_task_raises_service_unavailable_for_api_exception_409(self, mock_datetime, mock_job_name, mock_load_client):
        """Test that _run_task raises K8SServiceUnavailable when ApiException with status 409 occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123, pipeline_instance_id=456, environment=[])
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        
        # Create a new batch_api_v1 mock with ApiException
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Setup ApiException mock with status 409
        from kubernetes.client.rest import ApiException
        api_exception = ApiException(status=409, reason="Conflict")
        api_exception.body = 'Already exists'
        batch_api_mock.create_namespaced_job.side_effect = api_exception
        
        # Call the method and verify it raises K8SServiceUnavailable
        with self.assertRaises(K8SServiceUnavailable):
            self.handler._run_task(mock_work_request, mock_job)
            
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    def test_run_task_raises_service_unavailable_for_api_exception_400(self, mock_datetime, mock_job_name, mock_load_client):
        """Test that _run_task raises K8SServiceUnavailable when ApiException with status 400 occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123, pipeline_instance_id=456, environment=[])
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        
        # Create a new batch_api_v1 mock with ApiException
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Setup ApiException mock with status 400
        from kubernetes.client.rest import ApiException
        api_exception = ApiException(status=400, reason="Bad Request")
        api_exception.body = 'Invalid request'
        batch_api_mock.create_namespaced_job.side_effect = api_exception
        
        # Call the method and verify it raises K8SServiceUnavailable
        with self.assertRaises(K8SServiceUnavailable):
            self.handler._run_task(mock_work_request, mock_job)
            
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    def test_run_task_raises_should_sleep_for_other_api_exceptions(self, mock_datetime, mock_job_name, mock_load_client):
        """Test that _run_task raises QueueHandlerShouldSleep for other ApiException statuses."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123, pipeline_instance_id=456, environment=[])
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        
        # Create a new batch_api_v1 mock with ApiException
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Setup ApiException mock with status 500
        from kubernetes.client.rest import ApiException
        api_exception = ApiException(status=500, reason="Internal Server Error")
        batch_api_mock.create_namespaced_job.side_effect = api_exception
        
        # Call the method
        with self.assertRaises(QueueHandlerShouldSleep):
            self.handler._run_task(mock_work_request, mock_job)
            
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    def test_run_task_raises_connection_error_for_request_error(self, mock_datetime, mock_job_name, mock_load_client):
        """Test that _run_task raises K8SConnectionError when a RequestError occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123, pipeline_instance_id=456, environment={})
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        
        # Setup get_default_environment mock
        self.handler.get_default_environment = Mock(return_value=[])
        
        # Create a new batch_api_v1 mock with RequestError
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Setup RequestError mock
        request_error = urllib3.exceptions.RequestError("Connection error", "pool", "url")
        batch_api_mock.create_namespaced_job.side_effect = request_error
        
        # Call the method
        with self.assertRaises(K8SConnectionError):
            self.handler._run_task(mock_work_request, mock_job)
            
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch.object(K8SQueueHandler, K8SQueueHandler._run_task.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_job_definition.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_process_work_request_success(self, mock_set_task_status, mock_get_job_definition, mock_run_task, mock_datetime, mock_load_client):
        """Test that process_work_request method successfully processes a work request when a valid job definition exists."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123)
        mock_job = {'metadata': {'name': 'test-job'}}
        mock_get_job_definition.return_value = mock_job
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Call the method
        result = self.handler.process_work_request(mock_work_request, [])
        
        # Verify the results
        mock_get_job_definition.assert_called_with(mock_work_request)
        mock_run_task.assert_called_with(mock_work_request, mock_job)
        mock_set_task_status.assert_not_called()  # Should not be called on success path
        self.assertTrue(result)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_job_definition.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_process_work_request_no_job_definition(self, mock_set_task_status, mock_get_job_definition, mock_datetime, mock_load_client):
        """Test that process_work_request method sets the task status to FAILED when no job definition exists."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123)
        mock_get_job_definition.return_value = None
        mock_datetime.datetime.now.return_value = 'mock_datetime'
        
        # Call the method
        result = self.handler.process_work_request(mock_work_request, [])
        
        # Verify the results
        mock_get_job_definition.assert_called_with(mock_work_request)
        mock_set_task_status.assert_called_with(
            123, 
            StatusConstants.FAILED,
            start_date='mock_datetime',
            end_date='mock_datetime'
        )
        self.assertTrue(result)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._run_task.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_job_definition.__name__)
    def test_process_work_request_k8s_connection_error(self, mock_get_job_definition, mock_run_task, mock_load_client):
        """Test that process_work_request method raises QueueHandlerShouldSleep when a K8SConnectionError occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123)
        mock_job = {'metadata': {'name': 'test-job'}}
        mock_get_job_definition.return_value = mock_job
        mock_run_task.side_effect = K8SConnectionError("Connection error")
        
        # Call the method and verify it raises QueueHandlerShouldSleep
        with self.assertRaises(QueueHandlerShouldSleep):
            self.handler.process_work_request(mock_work_request, [])
            
        # Verify the mocks were called
        mock_get_job_definition.assert_called_once_with(mock_work_request)
        mock_run_task.assert_called_once_with(mock_work_request, mock_job)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._run_task.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_job_definition.__name__)
    def test_process_work_request_k8s_service_unavailable(self, mock_get_job_definition, mock_run_task, mock_load_client):
        """Test that process_work_request method raises QueueHandlerShouldSleep when a K8SServiceUnavailable occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123)
        mock_job = {'metadata': {'name': 'test-job'}}
        mock_get_job_definition.return_value = mock_job
        mock_run_task.side_effect = K8SServiceUnavailable("Service unavailable")
        
        # Call the method and verify it raises QueueHandlerShouldSleep
        with self.assertRaises(QueueHandlerShouldSleep):
            self.handler.process_work_request(mock_work_request, [])
            
        # Verify the mocks were called
        mock_get_job_definition.assert_called_once_with(mock_work_request)
        mock_run_task.assert_called_once_with(mock_work_request, mock_job)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    def test_get_running_pods_calls_list_namespaced_pod(self, mock_load_client):
        """Test that _get_running_pods calls list_namespaced_pod with the correct namespace."""
        # Setup mock
        self.handler._core_api_v1 = Mock()
        self.handler._core_api_v1.list_namespaced_pod.return_value = Mock(items=[])
        
        # Call the method
        self.handler._get_running_pods()
        
        # Verify list_namespaced_pod was called with the correct namespace
        self.handler._core_api_v1.list_namespaced_pod.assert_called_with(
            'cihub', label_selector='status=Running'
        )
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    def test_get_running_pods_uses_correct_label_selector(self, mock_load_client):
        """Test that _get_running_pods uses the correct label selector to filter running pods."""
        # Setup mock
        self.handler._core_api_v1 = Mock()
        self.handler._core_api_v1.list_namespaced_pod.return_value = Mock(items=[])
        
        # Call the method
        self.handler._get_running_pods()
        
        # Verify list_namespaced_pod was called with the correct label selector
        self.handler._core_api_v1.list_namespaced_pod.assert_called_with(
            'cihub', label_selector='status=Running'
        )
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    def test_get_running_pods_returns_pod_list_items(self, mock_load_client):
        """Test that _get_running_pods returns the items from the pod list."""
        # Setup mock
        mock_pod_list = Mock()
        mock_pod_list.items = ['pod1', 'pod2', 'pod3']
        
        self.handler._core_api_v1 = Mock()
        self.handler._core_api_v1.list_namespaced_pod.return_value = mock_pod_list
        
        # Call the method
        result = self.handler._get_running_pods()
        
        # Verify the result is the items from the pod list
        self.assertEqual(mock_pod_list.items, result)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_running_pods.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler.can_process_action_instance.__name__)
    def test_verify_still_working_checks_can_process_action_instance(self, mock_can_process, mock_job_name, mock_get_pods, mock_load_client):
        """Test that verify_still_working checks if the action instance can be processed."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'grain': 'test-job',
            'pipeline_instance_id': 456
        }
        
        # Setup mocks
        mock_can_process.return_value = True
        mock_get_pods.return_value = []
        
        # Call the method
        self.handler.verify_still_working([action_instance], [])
        
        # Verify can_process_action_instance was called with the action instance
        mock_can_process.assert_called_with(action_instance)
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_running_pods.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler.can_process_action_instance.__name__)
    def test_verify_still_working_gets_job_name(self, mock_can_process, mock_job_name, mock_get_pods, mock_load_client):
        """Test that verify_still_working generates the correct job name for the action instance."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'grain': 'test-job',
            'pipeline_instance_id': 456
        }
        
        # Setup mocks
        mock_can_process.return_value = True
        mock_get_pods.return_value = []
        
        # Call the method
        self.handler.verify_still_working([action_instance], [])
        
        # Verify _job_name was called with the correct parameters
        mock_job_name.assert_called_with('test-job', 456, 123)
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_running_pods.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler.can_process_action_instance.__name__)
    def test_verify_still_working_gets_running_pods(self, mock_can_process, mock_job_name, mock_get_pods, mock_load_client):
        """Test that verify_still_working retrieves the list of running pods."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'grain': 'test-job',
            'pipeline_instance_id': 456
        }
        
        # Setup mocks
        mock_can_process.return_value = True
        mock_get_pods.return_value = None
        
        # Call the method
        self.handler.verify_still_working([action_instance], [])
        
        # Verify _get_running_pods was called
        mock_get_pods.assert_called()
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_running_pods.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler.can_process_action_instance.__name__)
    def test_verify_still_working_resets_action_instance_when_pod_not_found(self, mock_can_process, mock_job_name, mock_get_pods, mock_load_client):
        """Test that verify_still_working resets action instances when their pods are not found."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'grain': 'test-job',
            'pipeline_instance_id': 456
        }
        
        # Setup mocks
        mock_can_process.return_value = True
        mock_job_name.return_value = 'test-job-456.123'
        
        # Create a mock pod with non-matching job name
        mock_pod = Mock()
        mock_pod.metadata = Mock()
        mock_pod.metadata.labels = {'job-name': 'other-job'}
        
        mock_get_pods.return_value = [mock_pod]
        
        # Reset the action_instance_service mock
        self.action_instance_service.reset_action_instance = Mock()
        
        # Call the method
        self.handler.verify_still_working([action_instance], [])
        
        # Verify reset_action_instance was called
        self.action_instance_service.reset_action_instance.assert_called_with(
            123, check_status=True
        )
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_running_pods.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler.can_process_action_instance.__name__)
    def test_verify_still_working_resets_action_instance_for_each_non_matching_pod(self, mock_can_process, mock_job_name, mock_get_pods, mock_load_client):
        """Test that verify_still_working resets action instances for each non-matching pod."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'grain': 'test-job',
            'pipeline_instance_id': 456
        }
        
        # Setup mocks
        mock_can_process.return_value = True
        mock_job_name.return_value = 'test-job-456.123'
        
        # Create mock pods with non-matching job names
        mock_pod1 = Mock()
        mock_pod1.metadata = Mock()
        mock_pod1.metadata.labels = {'job-name': 'other-job-1'}
        
        mock_pod2 = Mock()
        mock_pod2.metadata = Mock()
        mock_pod2.metadata.labels = {'job-name': 'other-job-2'}
        
        mock_get_pods.return_value = [mock_pod1, mock_pod2]
        
        # Reset the action_instance_service mock
        self.action_instance_service.reset_action_instance = Mock()
        
        # Call the method
        self.handler.verify_still_working([action_instance], [])
        
        # Verify reset_action_instance was called for each pod
        self.assertEqual(2, self.action_instance_service.reset_action_instance.call_count)
        self.action_instance_service.reset_action_instance.assert_has_calls([
            call(123, check_status=True),
            call(123, check_status=True)
        ])
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_running_pods.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler.can_process_action_instance.__name__)
    def test_verify_still_working_returns_empty_list_when_action_instance_reset(self, mock_can_process, mock_job_name, mock_get_pods, mock_load_client):
        """Test that verify_still_working returns an empty list when action instances are reset."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'grain': 'test-job',
            'pipeline_instance_id': 456
        }
        
        # Setup mocks
        mock_can_process.return_value = True
        mock_job_name.return_value = 'test-job-456.123'
        
        # Create a mock pod with non-matching job name
        mock_pod = Mock()
        mock_pod.metadata = Mock()
        mock_pod.metadata.labels = {'job-name': 'other-job'}
        
        mock_get_pods.return_value = [mock_pod]
        
        # Call the method
        result = self.handler.verify_still_working([action_instance], [])
        
        # Verify an empty list is returned
        self.assertEqual([], result)
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_running_pods.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler.can_process_action_instance.__name__)
    def test_verify_still_working_cannot_process(self, mock_can_process, mock_job_name, mock_get_pods, mock_load_client):
        """Test that verify_still_working skips action instances that cannot be processed."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'grain': 'test-job',
            'pipeline_instance_id': 456
        }
        
        # Setup mocks
        mock_can_process.return_value = False
        
        # Call the method
        result = self.handler.verify_still_working([action_instance], [])
        
        # Verify the results
        mock_can_process.assert_called_once_with(action_instance)
        
        # Should return empty list since action instance was skipped
        self.assertEqual([], result)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_running_pods.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler.can_process_action_instance.__name__)
    def test_verify_still_working_exception(self, mock_can_process, mock_job_name, mock_get_pods, mock_load_client):
        """Test that verify_still_working handles exceptions by adding the action instance to the failed list."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'grain': 'test-job',
            'pipeline_instance_id': 456
        }
        
        # Setup mocks
        mock_can_process.return_value = True
        mock_job_name.side_effect = Exception("Test exception")
        
        # Call the method
        result = self.handler.verify_still_working([action_instance], [])
        
        # Verify the results
        mock_can_process.assert_called_once_with(action_instance)
        mock_job_name.assert_called_once_with('test-job', 456, 123)
        
        # Should return the action instance in the failed list
        self.assertEqual([action_instance], result)
        
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_cancel_worker_extracts_job_name(self, mock_set_task_status, mock_load_client):
        """Test that cancel_worker correctly extracts the job name from the assigned_to field."""
        # Setup action instance with a specific assigned_to value
        action_instance = {
            'id': 123,
            'assigned_to': '--k8s--test-job-name'
        }
        
        # Mock the batch_api_v1 and core_api_v1 properties
        self.handler._batch_api_v1 = Mock()
        self.handler._core_api_v1 = Mock()
        self.handler._core_api_v1.list_namespaced_pod.return_value.items = []
        
        # Call the method
        self.handler.cancel_worker(action_instance)
        
        # Verify the job name was correctly extracted and used
        self.handler._batch_api_v1.read_namespaced_job.assert_called_with(
            'test-job-name', 'cihub'
        )
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_cancel_worker_uses_correct_namespace(self, mock_set_task_status, mock_load_client):
        """Test that cancel_worker uses the correct namespace (cihub) when interacting with Kubernetes."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'assigned_to': '--k8s--test-job-name'
        }
        
        # Mock the batch_api_v1 and core_api_v1 properties
        self.handler._batch_api_v1 = Mock()
        self.handler._core_api_v1 = Mock()
        self.handler._core_api_v1.list_namespaced_pod.return_value.items = []
        
        # Call the method
        self.handler.cancel_worker(action_instance)
        
        # Verify the correct namespace was used for all API calls
        self.handler._batch_api_v1.read_namespaced_job.assert_called_with(
            'test-job-name', 'cihub'
        )
        self.handler._core_api_v1.list_namespaced_pod.assert_called_with(
            'cihub', label_selector='job-name=test-job-name'
        )
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_cancel_worker_deletes_job(self, mock_set_task_status, mock_load_client):
        """Test that cancel_worker calls delete_namespaced_job to remove the Kubernetes job."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'assigned_to': '--k8s--test-job-name'
        }
        
        # Mock the batch_api_v1 and core_api_v1 properties
        self.handler._batch_api_v1 = Mock()
        self.handler._batch_api_v1.read_namespaced_job.return_value = Mock()  # Job exists
        self.handler._core_api_v1 = Mock()
        self.handler._core_api_v1.list_namespaced_pod.return_value.items = []
        
        # Call the method
        self.handler.cancel_worker(action_instance)
        
        # Verify delete_namespaced_job was called with the correct parameters
        self.handler._batch_api_v1.delete_namespaced_job.assert_called_with(
            'test-job-name', 'cihub'
        )
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_cancel_worker_deletes_pods(self, mock_set_task_status, mock_load_client):
        """Test that cancel_worker deletes all pods associated with the job."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'assigned_to': '--k8s--test-job-name'
        }
        
        # Mock the batch_api_v1 and core_api_v1 properties
        self.handler._batch_api_v1 = Mock()
        self.handler._batch_api_v1.read_namespaced_job.return_value = Mock()  # Job exists
        
        # Create mock pods
        pod1 = Mock()
        pod1.metadata.name = 'pod1'
        pod2 = Mock()
        pod2.metadata.name = 'pod2'
        
        self.handler._core_api_v1 = Mock()
        self.handler._core_api_v1.list_namespaced_pod.return_value.items = [pod1, pod2]
        
        # Call the method
        self.handler.cancel_worker(action_instance)
        
        # Verify delete_namespaced_pod was called for each pod
        self.handler._core_api_v1.delete_namespaced_pod.assert_has_calls([
            call('pod1', 'cihub'),
            call('pod2', 'cihub')
        ])
    
    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._set_task_status.__name__)
    def test_cancel_worker_sets_task_status_to_canceled(self, mock_set_task_status, mock_load_client):
        """Test that cancel_worker sets the task status to CANCELED."""
        # Setup action instance
        action_instance = {
            'id': 123,
            'assigned_to': '--k8s--test-job-name'
        }
        
        # Mock the batch_api_v1 and core_api_v1 properties
        self.handler._batch_api_v1 = Mock()
        self.handler._core_api_v1 = Mock()
        self.handler._core_api_v1.list_namespaced_pod.return_value.items = []
        
        # Call the method
        self.handler.cancel_worker(action_instance)
        
        # Verify the task status was set to CANCELED
        mock_set_task_status.assert_called_with(
            123, StatusConstants.CANCELED
        )

    @patch.object(K8SQueueHandler, K8SQueueHandler._get_grain_type_split.__name__)
    def test_get_job_definition_file_not_found(self, mock_grain_split):
        """
        Test that _get_job_definition method raises FileNotFoundError when the job definition file
        does not exist.
        """
        # Setup mocks
        work_request = Mock(grain='k8s://non-existent-job')
        mock_grain_split.return_value = ('k8s', 'non-existent-job')
        
        # Call the method and verify it raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            self.handler._get_job_definition(work_request)
        
        mock_grain_split.assert_called_with('k8s://non-existent-job')

    @patch.object(K8SQueueHandler, K8SQueueHandler._run_task.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._get_job_definition.__name__)
    def test_process_work_request_k8s_connection_error(self, mock_get_job_definition, mock_run_task):
        """Test that process_work_request method raises QueueHandlerShouldSleep when a K8SConnectionError occurs."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123)
        mock_job = {'metadata': {'name': 'test-job'}}
        mock_get_job_definition.return_value = mock_job
        mock_run_task.side_effect = K8SConnectionError("Connection error")
        
        # Call the method
        with self.assertRaises(QueueHandlerShouldSleep):
            self.handler.process_work_request(mock_work_request, [])
        
        # Verify the mocks were called
        mock_get_job_definition.assert_called_with(mock_work_request)
        mock_run_task.assert_called_with(mock_work_request, mock_job)

    @patch.object(K8SQueueHandler, K8SQueueHandler._load_k8s_client.__name__)
    @patch.object(K8SQueueHandler, K8SQueueHandler._job_name.__name__)
    @patch('rapid.workflow.queue_handlers.handlers.k8s_queue_handler.datetime')
    def test_run_task_raises_should_sleep_for_other_api_exceptions(self, mock_datetime, mock_job_name, mock_load_client):
        """Test that _run_task raises QueueHandlerShouldSleep for other ApiException statuses."""
        # Setup mocks
        mock_work_request = Mock(action_instance_id=123, pipeline_instance_id=456, environment=[])
        mock_job = {
            'metadata': {'name': 'test-job'},
            'spec': {
                'template': {
                    'spec': {
                        'containers': [{}]
                    }
                }
            }
        }
        mock_job_name.return_value = 'test-job-456.123'
        
        # Create a new batch_api_v1 mock with ApiException
        batch_api_mock = Mock()
        self.handler._batch_api_v1 = batch_api_mock
        
        # Setup ApiException mock with status 500
        from kubernetes.client.rest import ApiException
        api_exception = ApiException(status=500, reason="Internal Server Error")
        batch_api_mock.create_namespaced_job.side_effect = api_exception
        
        # Call the method and verify it raises QueueHandlerShouldSleep
        with self.assertRaises(QueueHandlerShouldSleep):
            self.handler._run_task(mock_work_request, mock_job)
