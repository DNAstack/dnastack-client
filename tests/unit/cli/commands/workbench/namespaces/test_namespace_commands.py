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


class TestGetDefaultDeprecation:
    """Tests for the get-default deprecation warning."""

    def setup_method(self):
        self.runner = CliRunner(mix_stderr=False)
        self.group = Group()
        init_namespace_commands(self.group)

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_emits_deprecation_warning_to_stderr(self, mock_get_client):
        mock_client = Mock()
        mock_config = Mock()
        mock_config.default_namespace = "my-namespace"
        mock_client.get_user_config.return_value = mock_config
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['get-default'])

        assert result.exit_code == 0
        assert "deprecated" in result.stderr.lower()
        assert "get-active" in result.stderr

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_stdout_still_contains_only_namespace(self, mock_get_client):
        mock_client = Mock()
        mock_config = Mock()
        mock_config.default_namespace = "my-namespace"
        mock_client.get_user_config.return_value = mock_config
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['get-default'])

        assert result.exit_code == 0
        assert result.output.strip() == "my-namespace"


class TestCreateCommand:
    """Tests for the create namespace CLI command."""

    def setup_method(self):
        self.runner = CliRunner()
        self.group = Group()
        init_namespace_commands(self.group)

        self.mock_namespace = Namespace(
            id="ns-new-123",
            name="New Namespace",
            description="A brand new namespace",
            created_at="2026-03-13T00:00:00Z",
            created_by="user@example.com",
            updated_at="2026-03-13T00:00:00Z",
            updated_by="user@example.com",
        )

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_create_with_name_only(self, mock_get_client):
        mock_client = Mock()
        mock_client.create_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['create', '--name', 'New Namespace'])

        assert result.exit_code == 0
        mock_client.create_namespace.assert_called_once_with(name="New Namespace", description=None)
        output = json.loads(result.output)
        assert output["id"] == "ns-new-123"
        assert output["name"] == "New Namespace"

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_create_with_name_and_description(self, mock_get_client):
        mock_client = Mock()
        mock_client.create_namespace.return_value = self.mock_namespace
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['create', '--name', 'New Namespace', '--description', 'A brand new namespace'])

        assert result.exit_code == 0
        mock_client.create_namespace.assert_called_once_with(name="New Namespace", description="A brand new namespace")

    @patch('dnastack.cli.commands.workbench.namespaces.commands.get_user_client')
    def test_create_requires_name(self, mock_get_client):
        result = self.runner.invoke(self.group, ['create'])

        assert result.exit_code != 0
