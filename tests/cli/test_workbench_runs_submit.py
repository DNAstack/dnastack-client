import json
import tempfile
from unittest import TestCase
from unittest.mock import Mock, patch
from click.testing import CliRunner

from dnastack.cli.commands.workbench.runs.commands import init_runs_commands
from dnastack.client.workbench.ewes.models import BatchRunRequest, BatchRunResponse, MinimalExtendedRun
from click import Group


class TestWorkbenchRunsSubmit(TestCase):
    """Unit tests for workbench runs submit command with focus on dependency handling"""
    
    def setUp(self):
        self.runner = CliRunner()
        self.mock_ewes_client = Mock()
        self.test_workflow_url = "workflow-id/version-1.0"
        self.test_engine_id = "test-engine-id"
        
        # Mock the submit_batch response
        self.mock_batch_response = BatchRunResponse(runs=[
            MinimalExtendedRun(run_id="run-1", state="QUEUED"),
            MinimalExtendedRun(run_id="run-2", state="QUEUED"),
            MinimalExtendedRun(run_id="run-3", state="QUEUED"),
        ])
        self.mock_ewes_client.submit_batch.return_value = self.mock_batch_response
        
        # Mock the list_engines response for default engine
        mock_engine = Mock()
        mock_engine.default = True
        mock_engine.id = self.test_engine_id
        self.mock_ewes_client.list_engines.return_value = [mock_engine]
        
        # Create command group
        self.group = Group()
        init_runs_commands(self.group)

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_batch_with_run_request_json_string(self, mock_get_client):
        """Test --run-request with inline JSON string containing dependencies"""
        mock_get_client.return_value = self.mock_ewes_client
        
        run_request_json = json.dumps({
            "workflow_params": {"test.hello.name": "from-json"},
            "tags": {"source": "json-string"},
            "dependencies": [
                {
                    "run_id": "12345678-1234-1234-1234-123456789012"
                }
            ]
        })
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url, '--run-request', run_request_json]
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify submit_batch was called
        self.mock_ewes_client.submit_batch.assert_called_once()
        
        # Get the actual BatchRunRequest that was submitted
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify the batch request structure
        self.assertIsInstance(batch_request, BatchRunRequest)
        self.assertEqual(batch_request.workflow_url, self.test_workflow_url)
        self.assertEqual(batch_request.engine_id, self.test_engine_id)
        self.assertEqual(len(batch_request.run_requests), 1)
        
        # Verify the run request details
        run_request = batch_request.run_requests[0]
        self.assertEqual(run_request.workflow_params, {"test.hello.name": "from-json"})
        self.assertEqual(run_request.tags, {"source": "json-string"})
        self.assertIsNotNone(run_request.dependencies)
        self.assertEqual(len(run_request.dependencies), 1)
        self.assertEqual(run_request.dependencies[0].run_id, "12345678-1234-1234-1234-123456789012")

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_batch_with_run_request_file(self, mock_get_client):
        """Test --run-request with file path containing dependencies"""
        mock_get_client.return_value = self.mock_ewes_client
        
        # Create a temporary file with run request
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "workflow_params": {"test.hello.name": "from-file"},
                "tags": {"source": "file"},
                "dependencies": [
                    {
                        "run_id": "file-dependency-id"
                    }
                ]
            }, f)
            temp_file_path = f.name
        
        try:
            result = self.runner.invoke(
                self.group,
                ['submit', '--url', self.test_workflow_url, '--run-request', f'@{temp_file_path}']
            )
            
            self.assertEqual(result.exit_code, 0)
            
            # Verify submit_batch was called
            self.mock_ewes_client.submit_batch.assert_called_once()
            
            # Get the actual BatchRunRequest
            batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
            
            # Verify the run request details
            self.assertEqual(len(batch_request.run_requests), 1)
            run_request = batch_request.run_requests[0]
            self.assertEqual(run_request.workflow_params, {"test.hello.name": "from-file"})
            self.assertEqual(run_request.tags, {"source": "file"})
            self.assertIsNotNone(run_request.dependencies)
            self.assertEqual(len(run_request.dependencies), 1)
            self.assertEqual(run_request.dependencies[0].run_id, "file-dependency-id")
        finally:
            import os
            os.unlink(temp_file_path)

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_batch_with_dollar_syntax_dependencies(self, mock_get_client):
        """Test --run-request with $ syntax for batch dependencies"""
        mock_get_client.return_value = self.mock_ewes_client
        
        request1 = json.dumps({
            "workflow_params": {"test.hello.name": "first"},
            "tags": {"order": "1"}
        })
        request2 = json.dumps({
            "workflow_params": {"test.hello.name": "second"},
            "tags": {"order": "2"},
            "dependencies": [
                {
                    "run_id": "$0"
                }
            ]
        })
        request3 = json.dumps({
            "workflow_params": {"test.hello.name": "third"},
            "tags": {"order": "3"},
            "dependencies": [
                {
                    "run_id": "$0"
                },
                {
                    "run_id": "$1"
                }
            ]
        })
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url, 
             '--run-request', request1,
             '--run-request', request2,
             '--run-request', request3]
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Get the actual BatchRunRequest
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify we have 3 run requests
        self.assertEqual(len(batch_request.run_requests), 3)
        
        # First request has no dependencies
        self.assertIsNone(batch_request.run_requests[0].dependencies)
        
        # Second request depends on first ($0)
        self.assertIsNotNone(batch_request.run_requests[1].dependencies)
        self.assertEqual(len(batch_request.run_requests[1].dependencies), 1)
        self.assertEqual(batch_request.run_requests[1].dependencies[0].run_id, "$0")
        
        # Third request depends on first ($0) and second ($1)
        self.assertIsNotNone(batch_request.run_requests[2].dependencies)
        self.assertEqual(len(batch_request.run_requests[2].dependencies), 2)
        self.assertEqual(batch_request.run_requests[2].dependencies[0].run_id, "$0")
        self.assertEqual(batch_request.run_requests[2].dependencies[1].run_id, "$1")

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_batch_mixed_params_and_run_requests(self, mock_get_client):
        """Test mixing --workflow-params and --run-request flags"""
        mock_get_client.return_value = self.mock_ewes_client
        
        run_request_json = json.dumps({
            "workflow_params": {"test.hello.name": "from-request"},
            "dependencies": [
                {
                    "run_id": "$1"  # Depends on second run (from --workflow-params)
                }
            ]
        })
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url,
             '--run-request', run_request_json,
             '--workflow-params', 'test.hello.name=from-params']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Get the actual BatchRunRequest
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify we have 2 run requests
        self.assertEqual(len(batch_request.run_requests), 2)
        
        # First run from --run-request has dependencies (depends on $1, the second run)
        self.assertEqual(batch_request.run_requests[0].workflow_params, {"test.hello.name": "from-request"})
        self.assertIsNotNone(batch_request.run_requests[0].dependencies)
        self.assertEqual(len(batch_request.run_requests[0].dependencies), 1)
        self.assertEqual(batch_request.run_requests[0].dependencies[0].run_id, "$1")
        
        # Second run from --workflow-params has no dependencies
        self.assertEqual(batch_request.run_requests[1].workflow_params, {"test.hello.name": "from-params"})
        self.assertIsNone(batch_request.run_requests[1].dependencies)

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_batch_with_dry_run(self, mock_get_client):
        """Test --dry-run flag shows the request without submitting"""
        mock_get_client.return_value = self.mock_ewes_client
        
        run_request_json = json.dumps({
            "workflow_params": {"test.hello.name": "dry-run-test"},
            "dependencies": [
                {
                    "run_id": "dependency-id"
                }
            ]
        })
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url,
             '--run-request', run_request_json,
             '--dry-run']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify submit_batch was NOT called
        self.mock_ewes_client.submit_batch.assert_not_called()
        
        # Verify the output contains the batch request
        output = json.loads(result.output)
        self.assertEqual(output["workflow_url"], self.test_workflow_url)
        self.assertEqual(len(output["run_requests"]), 1)
        self.assertEqual(output["run_requests"][0]["workflow_params"], {"test.hello.name": "dry-run-test"})
        self.assertEqual(len(output["run_requests"][0]["dependencies"]), 1)
        self.assertEqual(output["run_requests"][0]["dependencies"][0]["run_id"], "dependency-id")

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_batch_with_complex_dependencies(self, mock_get_client):
        """Test complex dependency scenarios"""
        mock_get_client.return_value = self.mock_ewes_client
        
        # Create a run request with multiple dependencies
        run_request_json = json.dumps({
            "workflow_params": {"test.hello.name": "complex"},
            "tags": {"type": "complex-dependencies"},
            "dependencies": [
                {
                    "run_id": "11111111-1111-1111-1111-111111111111"
                },
                {
                    "run_id": "22222222-2222-2222-2222-222222222222"
                },
                {
                    "run_id": "$0"
                }
            ]
        })
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url,
             '--workflow-params', 'test.hello.name=simple',  # First run
             '--run-request', run_request_json]              # Second run with dependencies
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Get the actual BatchRunRequest
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify the first run (from --run-request) has all three dependencies
        self.assertEqual(len(batch_request.run_requests), 2)
        dependencies = batch_request.run_requests[0].dependencies
        self.assertIsNotNone(dependencies)
        self.assertEqual(len(dependencies), 3)
        self.assertEqual(dependencies[0].run_id, "11111111-1111-1111-1111-111111111111")
        self.assertEqual(dependencies[1].run_id, "22222222-2222-2222-2222-222222222222")
        self.assertEqual(dependencies[2].run_id, "$0")