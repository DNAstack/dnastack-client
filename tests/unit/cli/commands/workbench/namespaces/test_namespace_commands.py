import json
from unittest.mock import Mock, patch
from click import Group
from click.testing import CliRunner

from dnastack.cli.commands.workbench.namespaces.commands import init_namespace_commands
from dnastack.client.workbench.workbench_user_service.models import Namespace


class TestGetActiveCommand:
    """Tests for the get-active namespace CLI command."""

    def setup_method(self):
        self.runner = CliRunner()
        self.group = Group()
        init_namespace_commands(self.group)

        self.mock_namespace = Namespace(
            id="ns-123",
            name="My Workspace",
            description="Test workspace",
            created_at="2026-01-01T00:00:00Z",
            created_by="system",
            updated_at="2026-01-01T00:00:00Z",
            updated_by="system",
        )

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_outputs_full_namespace_json(self, mock_get_client):
        mock_client = Mock()
        mock_client.get_active_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['get-active'])

        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["id"] == "ns-123"
        assert output["name"] == "My Workspace"
        assert output["description"] == "Test workspace"

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_id_flag_outputs_only_id(self, mock_get_client):
        mock_client = Mock()
        mock_client.get_active_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['get-active', '--id'])

        assert result.exit_code == 0
        assert result.output.strip() == "ns-123"


class TestSetActiveCommand:
    """Tests for the set-active namespace CLI command."""

    def setup_method(self):
        self.runner = CliRunner()
        self.group = Group()
        init_namespace_commands(self.group)

        self.mock_namespace = Namespace(
            id="ns-789",
            name="Switched Workspace",
        )

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_sets_active_namespace_and_outputs_json(self, mock_get_client):
        mock_client = Mock()
        mock_client.set_active_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['set-active', 'ns-789'])

        assert result.exit_code == 0
        mock_client.set_active_namespace.assert_called_once_with("ns-789")
        output = json.loads(result.output)
        assert output["id"] == "ns-789"
        assert output["name"] == "Switched Workspace"

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_requires_namespace_id_argument(self, mock_get_client):
        result = self.runner.invoke(self.group, ['set-active'])

        assert result.exit_code != 0
