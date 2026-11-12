import json
from unittest.mock import Mock, patch

from click import Group
from click.testing import CliRunner

from dnastack.cli.commands.workbench.users.commands import init_users_commands
from dnastack.client.workbench.workbench_user_service.models import WorkbenchUser
from dnastack.http.session import ClientError


class _UsersCommandTest:
    def setup_method(self):
        self.runner = CliRunner(mix_stderr=False)
        self.group = Group()
        init_users_commands(self.group)


class TestDescribeCommand(_UsersCommandTest):
    """Tests for the users describe CLI command."""

    @patch('dnastack.cli.commands.workbench.users.commands.get_user_client')
    def test_describes_each_user_as_json(self, mock_get_client):
        mock_client = Mock()
        mock_client.get_user.side_effect = [
            WorkbenchUser(id="user-1", email="alice@example.com", full_name="Alice"),
            WorkbenchUser(id="user-2", email="bob@example.com"),
        ]
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['describe', 'alice@example.com', 'user-2'])

        assert result.exit_code == 0
        assert [c.args for c in mock_client.get_user.call_args_list] == [("alice@example.com",), ("user-2",)]
        output = json.loads(result.stdout)
        assert [u["id"] for u in output] == ["user-1", "user-2"]
        assert output[0]["email"] == "alice@example.com"
        assert output[0]["full_name"] == "Alice"

    @patch('dnastack.cli.commands.workbench.users.commands.get_user_client')
    def test_not_found_reports_http_404_and_exits_non_zero(self, mock_get_client):
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "User not found"
        mock_client.get_user.side_effect = ClientError(mock_response)
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['describe', 'missing@example.com'])

        assert result.exit_code == 1
        assert "HTTP 404: User not found" in result.stderr
        assert result.stdout == ""

    @patch('dnastack.cli.commands.workbench.users.commands.get_user_client')
    def test_requires_email_or_id(self, mock_get_client):
        result = self.runner.invoke(self.group, ['describe'])

        assert result.exit_code == 2
        mock_get_client.assert_not_called()


class TestRegisterCommand(_UsersCommandTest):
    """Tests for the users register CLI command."""

    @patch('dnastack.cli.commands.workbench.users.commands.get_user_client')
    def test_registers_user_and_outputs_json(self, mock_get_client):
        mock_client = Mock()
        mock_client.register_user.return_value = WorkbenchUser(id="user-3", email="carol@example.com")
        mock_get_client.return_value = mock_client

        result = self.runner.invoke(self.group, ['register', '--email', 'carol@example.com'])

        assert result.exit_code == 0
        mock_client.register_user.assert_called_once_with("carol@example.com")
        output = json.loads(result.stdout)
        assert output["id"] == "user-3"
        assert output["email"] == "carol@example.com"

    @patch('dnastack.cli.commands.workbench.users.commands.get_user_client')
    def test_requires_email(self, mock_get_client):
        result = self.runner.invoke(self.group, ['register'])

        assert result.exit_code == 2
        assert "--email" in result.stderr
        mock_get_client.assert_not_called()
