"""Unit tests for workbench runs samples commands"""
import unittest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from click import Group

from dnastack.cli.commands.workbench.runs.samples.commands import init_samples_commands
from dnastack.client.workbench.ewes.models import SimpleSample, ExtendedRun, ExtendedRunRequest, ExtendedRunStatus


class TestRunsSamplesAddCommand(unittest.TestCase):
    """Unit tests for runs samples add command"""

    def setUp(self):
        self.runner = CliRunner()
        self.mock_ewes_client = Mock()

        self.group = Group()
        init_samples_commands(self.group)

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_add_samples_to_run(self, mock_get_client):
        """Test adding samples to a run preserves existing samples"""
        mock_get_client.return_value = self.mock_ewes_client

        existing_run = Mock(spec=ExtendedRun)
        existing_run.request = Mock(spec=ExtendedRunRequest)
        existing_run.request.samples = [SimpleSample(id='existing-1', storage_account_id='sa-1')]
        self.mock_ewes_client.get_run.return_value = existing_run

        mock_result = Mock(spec=ExtendedRunStatus)
        mock_result.model_dump.return_value = {'samples': []}
        self.mock_ewes_client.update_run_samples.return_value = mock_result

        result = self.runner.invoke(
            self.group,
            ['add', '--run-id', 'run-1', '--sample', 'new-1', '--storage-account', 'sa-1']
        )

        self.assertEqual(result.exit_code, 0)
        call_args = self.mock_ewes_client.update_run_samples.call_args
        samples = call_args[0][1]
        sample_ids = {s.id for s in samples}
        self.assertIn('existing-1', sample_ids)
        self.assertIn('new-1', sample_ids)

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_add_duplicate_sample_is_ignored(self, mock_get_client):
        """Test adding a sample that already exists doesn't duplicate it"""
        mock_get_client.return_value = self.mock_ewes_client

        existing_run = Mock(spec=ExtendedRun)
        existing_run.request = Mock(spec=ExtendedRunRequest)
        existing_run.request.samples = [SimpleSample(id='sample-1', storage_account_id='sa-1')]
        self.mock_ewes_client.get_run.return_value = existing_run

        mock_result = Mock(spec=ExtendedRunStatus)
        mock_result.model_dump.return_value = {'samples': []}
        self.mock_ewes_client.update_run_samples.return_value = mock_result

        result = self.runner.invoke(
            self.group,
            ['add', '--run-id', 'run-1', '--sample', 'sample-1', '--storage-account', 'sa-1']
        )

        self.assertEqual(result.exit_code, 0)
        call_args = self.mock_ewes_client.update_run_samples.call_args
        samples = call_args[0][1]
        self.assertEqual(len(samples), 1)

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_add_samples_to_run_without_existing(self, mock_get_client):
        """Test adding samples to a run with no existing samples"""
        mock_get_client.return_value = self.mock_ewes_client

        existing_run = Mock(spec=ExtendedRun)
        existing_run.request = Mock(spec=ExtendedRunRequest)
        existing_run.request.samples = None
        self.mock_ewes_client.get_run.return_value = existing_run

        mock_result = Mock(spec=ExtendedRunStatus)
        mock_result.model_dump.return_value = {'samples': []}
        self.mock_ewes_client.update_run_samples.return_value = mock_result

        result = self.runner.invoke(
            self.group,
            ['add', '--run-id', 'run-1', '--sample', 'new-1']
        )

        self.assertEqual(result.exit_code, 0)
        call_args = self.mock_ewes_client.update_run_samples.call_args
        samples = call_args[0][1]
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].id, 'new-1')

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_add_samples_missing_run_id(self, mock_get_client):
        """Test add samples fails without --run-id"""
        mock_get_client.return_value = self.mock_ewes_client

        result = self.runner.invoke(
            self.group,
            ['add', '--sample', 'sample-1']
        )

        self.assertNotEqual(result.exit_code, 0)


    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_add_existing_sample_updates_storage_account(self, mock_get_client):
        """Test that re-adding existing samples with --storage-account updates their storage_account_id"""
        mock_get_client.return_value = self.mock_ewes_client

        existing_run = Mock(spec=ExtendedRun)
        existing_run.request = Mock(spec=ExtendedRunRequest)
        existing_run.request.samples = [
            SimpleSample(id='sample-1', storage_account_id=None),
            SimpleSample(id='sample-2', storage_account_id=None),
        ]
        self.mock_ewes_client.get_run.return_value = existing_run

        mock_result = Mock(spec=ExtendedRunStatus)
        mock_result.model_dump.return_value = {'samples': []}
        self.mock_ewes_client.update_run_samples.return_value = mock_result

        result = self.runner.invoke(
            self.group,
            ['add', '--run-id', 'run-1', '--sample', 'sample-1', '--sample', 'sample-2', '--storage-account', 'sa-new']
        )

        self.assertEqual(result.exit_code, 0)
        call_args = self.mock_ewes_client.update_run_samples.call_args
        samples = call_args[0][1]
        self.assertEqual(len(samples), 2)
        for s in samples:
            self.assertEqual(s.storage_account_id, 'sa-new',
                             f"Sample {s.id} should have updated storage_account_id")

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_add_existing_sample_preserves_storage_account_when_not_provided(self, mock_get_client):
        """Test that re-adding existing samples WITHOUT --storage-account preserves their existing storage_account_id"""
        mock_get_client.return_value = self.mock_ewes_client

        existing_run = Mock(spec=ExtendedRun)
        existing_run.request = Mock(spec=ExtendedRunRequest)
        existing_run.request.samples = [
            SimpleSample(id='sample-1', storage_account_id='sa-original'),
        ]
        self.mock_ewes_client.get_run.return_value = existing_run

        mock_result = Mock(spec=ExtendedRunStatus)
        mock_result.model_dump.return_value = {'samples': []}
        self.mock_ewes_client.update_run_samples.return_value = mock_result

        result = self.runner.invoke(
            self.group,
            ['add', '--run-id', 'run-1', '--sample', 'sample-1']
        )

        self.assertEqual(result.exit_code, 0)
        call_args = self.mock_ewes_client.update_run_samples.call_args
        samples = call_args[0][1]
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].storage_account_id, 'sa-original',
                         "Existing storage_account_id should be preserved when --storage-account not provided")


class TestRunsSamplesRemoveCommand(unittest.TestCase):
    """Unit tests for runs samples remove command"""

    def setUp(self):
        self.runner = CliRunner()
        self.mock_ewes_client = Mock()

        self.group = Group()
        init_samples_commands(self.group)

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_remove_samples_from_run(self, mock_get_client):
        """Test removing samples from a run"""
        mock_get_client.return_value = self.mock_ewes_client

        existing_run = Mock(spec=ExtendedRun)
        existing_run.request = Mock(spec=ExtendedRunRequest)
        existing_run.request.samples = [
            SimpleSample(id='sample-1', storage_account_id='sa-1'),
            SimpleSample(id='sample-2', storage_account_id='sa-1'),
        ]
        self.mock_ewes_client.get_run.return_value = existing_run

        mock_result = Mock(spec=ExtendedRunStatus)
        mock_result.model_dump.return_value = {'samples': []}
        self.mock_ewes_client.update_run_samples.return_value = mock_result

        result = self.runner.invoke(
            self.group,
            ['remove', '--run-id', 'run-1', '--sample', 'sample-1']
        )

        self.assertEqual(result.exit_code, 0)
        call_args = self.mock_ewes_client.update_run_samples.call_args
        samples = call_args[0][1]
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].id, 'sample-2')

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_remove_multiple_samples(self, mock_get_client):
        """Test removing multiple samples at once"""
        mock_get_client.return_value = self.mock_ewes_client

        existing_run = Mock(spec=ExtendedRun)
        existing_run.request = Mock(spec=ExtendedRunRequest)
        existing_run.request.samples = [
            SimpleSample(id='sample-1', storage_account_id='sa-1'),
            SimpleSample(id='sample-2', storage_account_id='sa-1'),
            SimpleSample(id='sample-3', storage_account_id='sa-1'),
        ]
        self.mock_ewes_client.get_run.return_value = existing_run

        mock_result = Mock(spec=ExtendedRunStatus)
        mock_result.model_dump.return_value = {'samples': []}
        self.mock_ewes_client.update_run_samples.return_value = mock_result

        result = self.runner.invoke(
            self.group,
            ['remove', '--run-id', 'run-1', '--sample', 'sample-1', '--sample', 'sample-3']
        )

        self.assertEqual(result.exit_code, 0)
        call_args = self.mock_ewes_client.update_run_samples.call_args
        samples = call_args[0][1]
        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0].id, 'sample-2')

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_remove_samples_missing_run_id(self, mock_get_client):
        """Test remove samples fails without --run-id"""
        mock_get_client.return_value = self.mock_ewes_client

        result = self.runner.invoke(
            self.group,
            ['remove', '--sample', 'sample-1']
        )

        self.assertNotEqual(result.exit_code, 0)


class TestRunsSamplesClearCommand(unittest.TestCase):
    """Unit tests for runs samples clear command"""

    def setUp(self):
        self.runner = CliRunner()
        self.mock_ewes_client = Mock()

        self.group = Group()
        init_samples_commands(self.group)

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_clear_all_samples(self, mock_get_client):
        """Test clearing all samples from a run"""
        mock_get_client.return_value = self.mock_ewes_client

        mock_result = Mock(spec=ExtendedRunStatus)
        mock_result.model_dump.return_value = {'samples': []}
        self.mock_ewes_client.update_run_samples.return_value = mock_result

        result = self.runner.invoke(
            self.group,
            ['clear', '--run-id', 'run-1']
        )

        self.assertEqual(result.exit_code, 0)
        call_args = self.mock_ewes_client.update_run_samples.call_args
        samples = call_args[0][1]
        self.assertEqual(len(samples), 0)
        # get_run should NOT be called for clear
        self.mock_ewes_client.get_run.assert_not_called()

    @patch('dnastack.cli.commands.workbench.runs.samples.commands.get_ewes_client')
    def test_clear_samples_missing_run_id(self, mock_get_client):
        """Test clear samples fails without --run-id"""
        mock_get_client.return_value = self.mock_ewes_client

        result = self.runner.invoke(
            self.group,
            ['clear']
        )

        self.assertNotEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
