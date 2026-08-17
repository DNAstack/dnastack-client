"""Unit tests for workbench samples commands"""
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner
from click import Group

from dnastack.cli.commands.workbench.samples.commands import init_samples_commands
from dnastack.cli.commands.workbench.samples.attributes import attributes_command_group
from dnastack.cli.commands.workbench.samples.metadata import metadata_command_group
from dnastack.client.workbench.samples.models import SampleListOptions, Sex, PerspectiveType, \
    MetadataProcessingResponse, MetadataProcessingResult
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
        self.assertEqual(call_args.id, ['sample-123', 'sample-456'])
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


class TestSamplesAttributesCommands(unittest.TestCase):
    """Unit tests for the samples attributes get/set/clear commands"""

    def setUp(self):
        self.runner = CliRunner()
        self.mock_samples_client = Mock()
        self.group = Group()
        self.group.add_command(attributes_command_group)

    def _invoke(self, *args, stdin=None):
        return self.runner.invoke(self.group, ['attributes', *args], input=stdin)

    @patch('dnastack.cli.commands.workbench.samples.attributes.get_samples_client')
    def test_get_prints_the_stored_document_verbatim(self, mock_get_client):
        """Printed unparsed, so nulls, key order and types survive"""
        mock_get_client.return_value = self.mock_samples_client
        stored = '{"zeta": {"nested": null, "flag": true}, "alpha": 1, "id": "not-the-sample-id"}'
        self.mock_samples_client.get_sample_attributes.return_value = stored

        result = self._invoke('get', 'HG002')

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(), stored)
        self.mock_samples_client.get_sample_attributes.assert_called_once_with('HG002')

    @patch('dnastack.cli.commands.workbench.samples.attributes.get_samples_client')
    def test_get_prints_an_empty_object_when_the_sample_has_no_attributes(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client
        self.mock_samples_client.get_sample_attributes.return_value = '{}'

        result = self._invoke('get', 'HG002')

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.output.strip(), '{}')

    @patch('dnastack.cli.commands.workbench.samples.attributes.get_samples_client')
    def test_set_sends_a_json_literal_without_reserialising_it(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client
        self.mock_samples_client.replace_sample_attributes.return_value = '{}'
        document = '{"zeta": {"nested": null, "flag": true}, "alpha": 1.0}'

        result = self._invoke('set', 'HG002', document)

        self.assertEqual(result.exit_code, 0)
        self.mock_samples_client.replace_sample_attributes.assert_called_once_with('HG002', document)

    @patch('dnastack.cli.commands.workbench.samples.attributes.get_samples_client')
    def test_set_reads_the_document_from_a_file(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client
        self.mock_samples_client.replace_sample_attributes.return_value = '{}'

        with self.runner.isolated_filesystem():
            Path('bag.json').write_text('{"kit_lot": "A7-2291"}')
            result = self._invoke('set', 'HG002', '@bag.json')

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(self.mock_samples_client.replace_sample_attributes.call_args[0][1],
                         '{"kit_lot": "A7-2291"}')

    @patch('dnastack.cli.commands.workbench.samples.attributes.get_samples_client')
    def test_set_rejects_a_bulk_document_and_points_at_the_upload_command(self, mock_get_client):
        """A sample-id-keyed document would otherwise nest the whole cohort under one sample"""
        mock_get_client.return_value = self.mock_samples_client

        with self.runner.isolated_filesystem():
            Path('cohort.attributes.json').write_text('{"HG002": {"kit_lot": "A7-2291"}}')
            result = self._invoke('set', 'HG002', '@cohort.attributes.json')

        self.assertEqual(result.exit_code, 1)
        self.assertIn('samples metadata upload', result.output)
        self.mock_samples_client.replace_sample_attributes.assert_not_called()

    @patch('dnastack.cli.commands.workbench.samples.attributes.get_samples_client')
    def test_set_suggests_the_at_prefix_when_given_a_bare_path(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client

        with self.runner.isolated_filesystem():
            Path('bag.json').write_text('{"kit_lot": "A7-2291"}')
            result = self._invoke('set', 'HG002', 'bag.json')

        self.assertEqual(result.exit_code, 1)
        self.assertIn('Did you mean @bag.json?', result.output)
        self.mock_samples_client.replace_sample_attributes.assert_not_called()

    @patch('dnastack.cli.commands.workbench.samples.attributes.get_samples_client')
    def test_set_rejects_json_that_is_not_an_object(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client

        result = self._invoke('set', 'HG002', '[1, 2]')

        self.assertEqual(result.exit_code, 1)
        self.assertIn('must be a JSON object', result.output)
        self.mock_samples_client.replace_sample_attributes.assert_not_called()

    @patch('dnastack.cli.commands.workbench.samples.attributes.get_samples_client')
    def test_clear_replaces_the_attributes_with_an_empty_object(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client
        self.mock_samples_client.replace_sample_attributes.return_value = '{}'

        result = self._invoke('clear', 'HG002', '--force')

        self.assertEqual(result.exit_code, 0)
        self.mock_samples_client.replace_sample_attributes.assert_called_once_with('HG002', '{}')

    @patch('dnastack.cli.commands.workbench.samples.attributes.get_samples_client')
    def test_clear_does_nothing_when_the_confirmation_is_declined(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client

        result = self._invoke('clear', 'HG002', stdin='n\n')

        self.assertEqual(result.exit_code, 0)
        self.mock_samples_client.replace_sample_attributes.assert_not_called()


class TestSamplesMetadataUploadCommand(unittest.TestCase):
    """Unit tests for the samples metadata upload command"""

    def setUp(self):
        self.runner = CliRunner()
        self.mock_samples_client = Mock()
        self.group = Group()
        self.group.add_command(metadata_command_group)

    def _respond_with(self, *results):
        self.mock_samples_client.upload_metadata.return_value = MetadataProcessingResponse(
            results=[MetadataProcessingResult(**result) for result in results]
        )

    def _invoke(self, *args, files=('cohort.ped',), contents='#ped\n'):
        with self.runner.isolated_filesystem():
            for name in files:
                Path(name).write_text(contents)
            return self.runner.invoke(self.group, ['metadata', 'upload', *files, *args])

    @patch('dnastack.cli.commands.workbench.samples.metadata.get_samples_client')
    def test_upload_prints_a_row_per_file_and_exits_zero_when_every_file_applied(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client
        self._respond_with(
            {'fileName': 'cohort.ped', 'outcome': 'SUCCESS', 'sampleIds': ['HG002', 'HG003']},
            {'fileName': 'lab.attributes.json', 'outcome': 'SUCCESS', 'sampleIds': ['HG004']},
        )

        result = self._invoke(files=('cohort.ped', 'lab.attributes.json'))

        self.assertEqual(result.exit_code, 0)
        printed = json.loads(result.output)
        self.assertEqual([row['file_name'] for row in printed['results']],
                         ['cohort.ped', 'lab.attributes.json'])
        self.assertEqual([row['sample_ids'] for row in printed['results']],
                         [['HG002', 'HG003'], ['HG004']])

    @patch('dnastack.cli.commands.workbench.samples.metadata.get_samples_client')
    def test_upload_exits_two_when_a_file_applied_only_some_of_its_samples(self, mock_get_client):
        """The service reports SUCCESS with errors when part of a file landed"""
        mock_get_client.return_value = self.mock_samples_client
        self._respond_with({
            'fileName': 'lab.attributes.json',
            'outcome': 'SUCCESS',
            'sampleIds': ['HG002'],
            'errors': ['HG999: Sample does not exist'],
        })

        result = self._invoke(files=('lab.attributes.json',), contents='{"HG002": {}}')

        self.assertEqual(result.exit_code, 2)
        self.assertIn('HG999: Sample does not exist', result.output)

    @patch('dnastack.cli.commands.workbench.samples.metadata.get_samples_client')
    def test_upload_exits_two_when_one_file_failed_and_another_applied(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client
        self._respond_with(
            {'fileName': 'cohort.ped', 'outcome': 'SUCCESS', 'sampleIds': ['HG002']},
            {'fileName': 'broken.json', 'outcome': 'FAILED', 'sampleIds': [],
             'errors': ['Not a phenopacket']},
        )

        result = self._invoke(files=('cohort.ped', 'broken.json'))

        self.assertEqual(result.exit_code, 2)

    @patch('dnastack.cli.commands.workbench.samples.metadata.get_samples_client')
    def test_upload_exits_one_when_no_sample_was_written(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client
        self._respond_with({'fileName': 'broken.json', 'outcome': 'FAILED', 'sampleIds': [],
                            'errors': ['Not a phenopacket']})

        result = self._invoke(files=('broken.json',))

        self.assertEqual(result.exit_code, 1)
        self.assertIn('No samples were written', result.output)

    @patch('dnastack.cli.commands.workbench.samples.metadata.get_samples_client')
    def test_upload_sends_each_file_under_the_name_the_user_gave_it(self, mock_get_client):
        """The service dispatches on file name, so the CLI must not rewrite it"""
        mock_get_client.return_value = self.mock_samples_client
        self._respond_with({'fileName': 'lab.attributes.json', 'outcome': 'SUCCESS',
                            'sampleIds': ['HG002']})

        result = self._invoke(files=('lab.attributes.json',), contents='{"HG002": {}}')

        self.assertEqual(result.exit_code, 0)
        sent = self.mock_samples_client.upload_metadata.call_args.kwargs['files']
        self.assertEqual([path.name for path in sent], ['lab.attributes.json'])

    @patch('dnastack.cli.commands.workbench.samples.metadata.get_samples_client')
    def test_upload_overwrites_existing_values_unless_preserve_existing_is_given(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client
        self._respond_with({'fileName': 'cohort.ped', 'outcome': 'SUCCESS', 'sampleIds': ['HG002']})

        self._invoke()
        self.assertIs(self.mock_samples_client.upload_metadata.call_args.kwargs['preserve_existing'], False)

        self._invoke('--preserve-existing')
        self.assertIs(self.mock_samples_client.upload_metadata.call_args.kwargs['preserve_existing'], True)

    @patch('dnastack.cli.commands.workbench.samples.metadata.get_samples_client')
    def test_upload_exits_one_when_the_service_rejects_an_empty_attributes_entry(self, mock_get_client):
        """The upload path rejects an empty object per sample, so it cannot clear a bag"""
        mock_get_client.return_value = self.mock_samples_client
        self._respond_with({
            'fileName': 'clear.attributes.json',
            'outcome': 'FAILED',
            'sampleIds': [],
            'errors': ['HG002: No attributes given for this sample'],
        })

        result = self._invoke(files=('clear.attributes.json',), contents='{"HG002": {}}')

        self.assertEqual(result.exit_code, 1)
        self.assertIn('No attributes given for this sample', result.output)

    @patch('dnastack.cli.commands.workbench.samples.metadata.get_samples_client')
    def test_upload_rejects_an_unrecognized_file_name_without_calling_the_service(self, mock_get_client):
        mock_get_client.return_value = self.mock_samples_client

        result = self._invoke(files=('cohort.txt',))

        self.assertEqual(result.exit_code, 1)
        self.assertIn('cohort.txt is not a metadata file', result.output)
        self.assertIn('*.attributes.json', result.output)
        self.mock_samples_client.upload_metadata.assert_not_called()


if __name__ == '__main__':
    unittest.main()