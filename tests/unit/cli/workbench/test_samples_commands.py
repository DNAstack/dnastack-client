"""Unit tests for workbench samples commands"""
import unittest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from click import Group

from dnastack.cli.commands.workbench.samples.commands import init_samples_commands
from dnastack.client.workbench.samples.models import SampleListOptions, Sex, PerspectiveType
from dnastack.client.workbench.common.models import State
from dnastack.client.workbench.storage.models import PlatformType


class TestSamplesListCommand(unittest.TestCase):
    """Unit tests for samples list command with comprehensive filtering options"""
    
    def setUp(self):
        self.runner = CliRunner()
        self.mock_samples_client = Mock()
        
        # Mock sample data based on real API response

        self.mock_samples = [
            {
                "id": "HG0005",
                "affected_status": None,
                "created_at": "2024-10-21T21:06:51.604018+00:00",
                "family_id": "FAM001",
                "father_id": None,
                "has_been_analyzed": False,
                "last_updated_at": "2024-10-21T21:06:51.604018+00:00",
                "metrics": {"file_count": 0, "instrument_types": []},
                "mother_id": None,
                "phenotypes": [],
                "runs": [],
                "sex": None
            },
            {
                "id": "PL15929-01",
                "affected_status": None,
                "created_at": "2024-12-20T20:42:54.491703+00:00",
                "family_id": "FAM02",
                "father_id": None,
                "has_been_analyzed": True,
                "last_updated_at": "2024-12-20T20:42:54.491703+00:00",
                "metrics": {"file_count": 1, "instrument_types": ["Revio"]},
                "mother_id": None,
                "phenotypes": [
                    {
                        "created_at": None,
                        "last_updated_at": None,
                        "type": {"id": "HP:0000118", "label": "Phenotypic abnormality"}
                    }
                ],
                "runs": [
                    {
                        "run_id": "0ccbe05f-0354-494c-84da-421e23df430d",
                        "state": "COMPLETE",
                        "workflow_id": "3377e02b-77d9-443a-9c21-58758069db2a",
                        "workflow_name": "DEBUG ECHO 2"
                    }
                ],
                "sex": "MALE"
            }
        ]
        self.mock_samples_client.list_samples.return_value = self.mock_samples
        
        # Create command group
        self.group = Group()
        init_samples_commands(self.group)

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_basic(self, mock_get_client):
        """Test basic samples list command"""
        mock_get_client.return_value = self.mock_samples_client
        
        result = self.runner.invoke(self.group, ['list'])
        
        self.assertEqual(result.exit_code, 0)
        self.mock_samples_client.list_samples.assert_called_once()
        
        # Verify that basic SampleListOptions was passed
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        self.assertIsInstance(call_args, SampleListOptions)

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_with_pagination(self, mock_get_client):
        """Test samples list with pagination parameters"""
        mock_get_client.return_value = self.mock_samples_client

        result = self.runner.invoke(
            self.group, 
            ['list', '--max-results', '50', '--page', '1', '--page-size', '25']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify pagination parameters were passed correctly
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        self.assertEqual(call_args.page, 1)
        self.assertEqual(call_args.page_size, 25)

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_with_storage_filters(self, mock_get_client):
        """Test samples list with storage-related filters"""
        mock_get_client.return_value = self.mock_samples_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', 
             '--storage-id', 'storage-123',
             '--platform-type', 'pacbio',
             '--instrument-id', 'instrument-456']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify storage filters were passed correctly
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        self.assertEqual(call_args.storage_id, 'storage-123')
        self.assertEqual(call_args.platform_type, PlatformType.pacbio)
        self.assertEqual(call_args.instrument_id, 'instrument-456')

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_with_workflow_filters(self, mock_get_client):
        """Test samples list with workflow-related filters"""
        mock_get_client.return_value = self.mock_samples_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', 
             '--workflow', 'workflow-id-123',
             '--workflow-version', 'version-456',
             '--state', 'COMPLETE',
             '--state', 'RUNNING']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify workflow filters were passed correctly
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        self.assertEqual(call_args.workflow_id, 'workflow-id-123')
        self.assertEqual(call_args.workflow_version_id, 'version-456')
        self.assertEqual(call_args.states, [State.COMPLETE, State.RUNNING])

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_with_family_and_sample_filters(self, mock_get_client):
        """Test samples list with family and sample ID filters"""
        mock_get_client.return_value = self.mock_samples_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', 
             '--family-id', 'family-1',
             '--family-id', 'family-2',
             '--sample', 'sample-123',
             '--sample', 'sample-456',
             '--sex', 'MALE',
             '--sex', 'FEMALE']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify filters were passed correctly
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        self.assertEqual(call_args.family_id, ['family-1', 'family-2'])
        self.assertEqual(call_args.sample_id, ['sample-123', 'sample-456'])
        # Note: Sex enum handling should be case-insensitive based on our CaseInsensitiveEnum
        self.assertIn(Sex.male, call_args.sexes)
        self.assertIn(Sex.female, call_args.sexes)

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_with_date_filters(self, mock_get_client):
        """Test samples list with date-based filters"""
        mock_get_client.return_value = self.mock_samples_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', 
             '--created-since', '2023-01-01',
             '--created-until', '2023-12-31']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify date filters were passed correctly with proper ISO formatting
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        self.assertEqual(call_args.since, '2023-01-01T00:00:00.000Z')
        self.assertEqual(call_args.until, '2023-12-31T23:59:59.999Z')

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_with_datetime_filters(self, mock_get_client):
        """Test samples list with datetime-based filters (already in ISO format)"""
        mock_get_client.return_value = self.mock_samples_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', 
             '--created-since', '2023-01-01T10:30:00.000Z',
             '--created-until', '2023-12-31T15:45:30.000Z']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify datetime filters are passed through unchanged when already in ISO format
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        self.assertEqual(call_args.since, '2023-01-01T10:30:00.000Z')
        self.assertEqual(call_args.until, '2023-12-31T15:45:30.000Z')

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_with_analysis_convenience_flags(self, mock_get_client):
        """Test samples list with analyzed/not-analyzed convenience flags"""
        mock_get_client.return_value = self.mock_samples_client
        
        # Test --analyzed flag
        result = self.runner.invoke(self.group, ['list', '--analyzed'])
        self.assertEqual(result.exit_code, 0)
        
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        expected_analyzed_states = [State.QUEUED, State.INITIALIZING, State.RUNNING, State.COMPLETE]
        self.assertEqual(call_args.states, expected_analyzed_states)
        
        # Reset mock
        self.mock_samples_client.reset_mock()
        
        # Test --not-analyzed flag
        result = self.runner.invoke(self.group, ['list', '--not-analyzed'])
        self.assertEqual(result.exit_code, 0)
        
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        self.assertEqual(call_args.states, [State.NOT_PROCESSED])

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_with_perspective_and_search(self, mock_get_client):
        """Test samples list with perspective and search filters"""
        mock_get_client.return_value = self.mock_samples_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', 
             '--perspective', 'workflow',
             '--workflow', 'workflow-123',  # Required when perspective is workflow
             '--search', 'test-sample']
        )
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify filters were passed correctly
        call_args = self.mock_samples_client.list_samples.call_args[0][0]
        self.assertEqual(call_args.perspective, PerspectiveType.workflow)
        self.assertEqual(call_args.workflow_id, 'workflow-123')
        self.assertEqual(call_args.search, 'test-sample')

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_list_samples_workflow_perspective_validation(self, mock_get_client):
        """Test that workflow perspective requires workflow-id"""
        mock_get_client.return_value = self.mock_samples_client
        
        result = self.runner.invoke(
            self.group, 
            ['list', '--perspective', 'workflow']
        )
        
        # Should fail because workflow-id is required with workflow perspective
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('workflow-id is required', result.output)

    @patch('dnastack.cli.commands.workbench.samples.commands.get_samples_client')
    def test_describe_sample(self, mock_get_client):
        """Test describe sample command"""
        mock_get_client.return_value = self.mock_samples_client
        mock_sample = {
            "id": "sample-123", 
            "sex": "MALE",
            "has_been_analyzed": False,
            "created_at": "2024-10-21T21:06:51.604018+00:00"
        }
        self.mock_samples_client.get_sample.return_value = mock_sample
        
        result = self.runner.invoke(self.group, ['describe', 'sample-123'])
        
        self.assertEqual(result.exit_code, 0)
        self.mock_samples_client.get_sample.assert_called_once_with('sample-123')


if __name__ == '__main__':
    unittest.main()