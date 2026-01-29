"""Unit tests for workbench runs hooks commands"""
import unittest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from click import Group

from dnastack.cli.commands.workbench.runs.hooks.commands import init_hooks_commands
from dnastack.client.workbench.ewes.models import Hook, HookListResponse


class TestHooksListCommand(unittest.TestCase):
    """Unit tests for hooks list command"""

    def setUp(self):
        self.runner = CliRunner()
        self.mock_ewes_client = Mock()

        self.mock_hooks_response = HookListResponse(
            hooks=[
                Hook(id="hook-1", type="LAUNCH_RUN", state="COMPLETE"),
                Hook(id="hook-2", type="INGEST_VARIANTS", state="PENDING"),
            ],
            pagination=None,
        )
        self.mock_ewes_client.list_hooks.return_value = self.mock_hooks_response

        self.group = Group()
        init_hooks_commands(self.group)

    @patch('dnastack.cli.commands.workbench.runs.hooks.commands.get_ewes_client')
    def test_list_hooks(self, mock_get_client):
        """Test hooks list returns hooks for a run"""
        mock_get_client.return_value = self.mock_ewes_client

        result = self.runner.invoke(
            self.group,
            ['list', '--run-id', 'run-123']
        )

        self.assertEqual(result.exit_code, 0)
        self.mock_ewes_client.list_hooks.assert_called_once_with('run-123')

    @patch('dnastack.cli.commands.workbench.runs.hooks.commands.get_ewes_client')
    def test_list_hooks_missing_run_id(self, mock_get_client):
        """Test hooks list fails without --run-id"""
        mock_get_client.return_value = self.mock_ewes_client

        result = self.runner.invoke(
            self.group,
            ['list']
        )

        self.assertNotEqual(result.exit_code, 0)


class TestHooksDescribeCommand(unittest.TestCase):
    """Unit tests for hooks describe command"""

    def setUp(self):
        self.runner = CliRunner()
        self.mock_ewes_client = Mock()

        self.mock_hook = Hook(
            id="hook-1",
            type="LAUNCH_RUN",
            state="COMPLETE",
            config={"run_request": {"workflow_url": "my-workflow"}},
            result_data={"child_run_id": "run-456"},
        )
        self.mock_ewes_client.get_hook.return_value = self.mock_hook

        self.group = Group()
        init_hooks_commands(self.group)

    @patch('dnastack.cli.commands.workbench.runs.hooks.commands.get_ewes_client')
    def test_describe_hook(self, mock_get_client):
        """Test hooks describe returns a specific hook"""
        mock_get_client.return_value = self.mock_ewes_client

        result = self.runner.invoke(
            self.group,
            ['describe', 'hook-1', '--run-id', 'run-123']
        )

        self.assertEqual(result.exit_code, 0)
        self.mock_ewes_client.get_hook.assert_called_once_with('run-123', 'hook-1')

    @patch('dnastack.cli.commands.workbench.runs.hooks.commands.get_ewes_client')
    def test_describe_hook_missing_run_id(self, mock_get_client):
        """Test hooks describe fails without --run-id"""
        mock_get_client.return_value = self.mock_ewes_client

        result = self.runner.invoke(
            self.group,
            ['describe', 'hook-1']
        )

        self.assertNotEqual(result.exit_code, 0)

    @patch('dnastack.cli.commands.workbench.runs.hooks.commands.get_ewes_client')
    def test_describe_hook_missing_hook_id(self, mock_get_client):
        """Test hooks describe fails without positional hook-id"""
        mock_get_client.return_value = self.mock_ewes_client

        result = self.runner.invoke(
            self.group,
            ['describe', '--run-id', 'run-123']
        )

        self.assertNotEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()