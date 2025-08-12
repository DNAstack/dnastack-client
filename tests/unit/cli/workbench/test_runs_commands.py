"""Unit tests for workbench runs commands"""
import unittest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from click import Group

from dnastack.cli.commands.workbench.runs.commands import init_runs_commands
from dnastack.client.workbench.ewes.models import (
    ExtendedRunListOptions, BatchRunRequest, BatchRunResponse, 
    MinimalExtendedRun
)
from dnastack.client.workbench.common.models import State


class TestRunsListCommand(unittest.TestCase):
    """Unit tests for runs list command with new filtering options"""
    
    def setUp(self):
        self.runner = CliRunner()
        self.mock_ewes_client = Mock()
        
        # Mock runs data
        self.mock_runs = [
            {
                "run_id": "run-1", 
                "state": "COMPLETE",
                "samples": [{"id": "sample-1", "storage_account_id": "storage-1"}]
            },
            {
                "run_id": "run-2", 
                "state": "RUNNING",
                "samples": [{"id": "sample-2", "storage_account_id": "storage-2"}]
            }
        ]
        self.mock_ewes_client.list_runs.return_value = self.mock_runs
        
        # Create command group
        self.group = Group()
        init_runs_commands(self.group)

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_list_runs_with_sample_filter(self, mock_get_client):
        """Test runs list with sample ID filter"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', '--sample', 'sample-1', '--sample', 'sample-2']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify sample filters were passed correctly
        call_args = self.mock_ewes_client.list_runs.call_args[0][0]
        self.assertIsInstance(call_args, ExtendedRunListOptions)
        self.assertEqual(call_args.sample_ids, ['sample-1', 'sample-2'])

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_list_runs_with_storage_account_filter(self, mock_get_client):
        """Test runs list with storage account filter"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', '--storage-account', 'storage-123']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify storage account filter was passed correctly
        call_args = self.mock_ewes_client.list_runs.call_args[0][0]
        self.assertEqual(call_args.storage_account_id, 'storage-123')

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_list_runs_with_combined_filters(self, mock_get_client):
        """Test runs list with both sample and storage account filters"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', 
             '--sample', 'sample-1', 
             '--sample', 'sample-2',
             '--storage-account', 'storage-123',
             '--state', 'COMPLETE']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify all filters were passed correctly
        call_args = self.mock_ewes_client.list_runs.call_args[0][0]
        self.assertEqual(call_args.sample_ids, ['sample-1', 'sample-2'])
        self.assertEqual(call_args.storage_account_id, 'storage-123')
        self.assertEqual(call_args.state, [State.COMPLETE])


class TestRunsSubmitCommand(unittest.TestCase):
    """Unit tests for runs submit command with new sample options"""
    
    def setUp(self):
        self.runner = CliRunner()
        self.mock_ewes_client = Mock()
        self.test_workflow_url = "workflow-id/version-1.0"
        self.test_engine_id = "test-engine-id"
        
        # Mock the submit_batch response
        self.mock_batch_response = BatchRunResponse(runs=[
            MinimalExtendedRun(run_id="run-1", state="QUEUED"),
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
    def test_submit_with_new_sample_flag(self, mock_get_client):
        """Test runs submit with new --sample flag (preferred over --samples)"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url, 
             '--sample', 'sample-1', 
             '--sample', 'sample-2']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify submit_batch was called
        self.mock_ewes_client.submit_batch.assert_called_once()
        
        # Get the actual BatchRunRequest that was submitted
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify the batch request structure
        self.assertIsInstance(batch_request, BatchRunRequest)
        self.assertEqual(batch_request.workflow_url, self.test_workflow_url)
        self.assertEqual(len(batch_request.samples), 2)
        
        # Verify the samples
        self.assertEqual(batch_request.samples[0].id, 'sample-1')
        self.assertEqual(batch_request.samples[1].id, 'sample-2')

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_with_sample_and_storage_account(self, mock_get_client):
        """Test runs submit with --sample and --storage-account flags"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url, 
             '--sample', 'sample-1', 
             '--sample', 'sample-2',
             '--storage-account', 'storage-123']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Get the actual BatchRunRequest that was submitted
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify the samples have the storage account ID
        self.assertEqual(len(batch_request.samples), 2)
        self.assertEqual(batch_request.samples[0].id, 'sample-1')
        self.assertEqual(batch_request.samples[0].storage_account_id, 'storage-123')
        self.assertEqual(batch_request.samples[1].id, 'sample-2')
        self.assertEqual(batch_request.samples[1].storage_account_id, 'storage-123')

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_with_deprecated_samples_flag(self, mock_get_client):
        """Test runs submit with deprecated --samples flag (backward compatibility)"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url, 
             '--samples', 'sample-1,sample-2,sample-3']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Get the actual BatchRunRequest that was submitted
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify the samples were parsed from the comma-separated list
        self.assertEqual(len(batch_request.samples), 3)
        self.assertEqual(batch_request.samples[0].id, 'sample-1')
        self.assertEqual(batch_request.samples[1].id, 'sample-2')
        self.assertEqual(batch_request.samples[2].id, 'sample-3')

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_with_both_sample_flags_prefer_new(self, mock_get_client):
        """Test that new --sample flag takes precedence over deprecated --samples"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url, 
             '--sample', 'sample-new-1',
             '--sample', 'sample-new-2', 
             '--samples', 'sample-old-1,sample-old-2']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Get the actual BatchRunRequest that was submitted
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify the new --sample flags were used, not the deprecated --samples
        self.assertEqual(len(batch_request.samples), 2)
        self.assertEqual(batch_request.samples[0].id, 'sample-new-1')
        self.assertEqual(batch_request.samples[1].id, 'sample-new-2')

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_with_dry_run_and_samples(self, mock_get_client):
        """Test runs submit with dry run and samples"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url, 
             '--sample', 'sample-1',
             '--storage-account', 'storage-123',
             '--dry-run']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify submit_batch was NOT called for dry run
        self.mock_ewes_client.submit_batch.assert_not_called()
        
        # Verify the dry run output contains the expected structure
        import json
        output = json.loads(result.output)
        self.assertEqual(output["workflow_url"], self.test_workflow_url)
        self.assertEqual(len(output["samples"]), 1)
        self.assertEqual(output["samples"][0]["id"], "sample-1")
        self.assertEqual(output["samples"][0]["storage_account_id"], "storage-123")

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_without_samples(self, mock_get_client):
        """Test runs submit without any samples (should work)"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url, 
             '--workflow-params', 'test.param=value']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Get the actual BatchRunRequest that was submitted
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify no samples were added
        self.assertIsNone(batch_request.samples)

    @patch('dnastack.cli.commands.workbench.runs.commands.get_ewes_client')
    def test_submit_storage_account_without_samples(self, mock_get_client):
        """Test that storage account flag without samples still works"""
        mock_get_client.return_value = self.mock_ewes_client
        
        result = self.runner.invoke(
            self.group,
            ['submit', '--url', self.test_workflow_url,
             '--storage-account', 'storage-123']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Get the actual BatchRunRequest that was submitted
        batch_request = self.mock_ewes_client.submit_batch.call_args[0][0]
        
        # Verify no samples were added when no sample IDs provided
        self.assertIsNone(batch_request.samples)


if __name__ == '__main__':
    unittest.main()