import json
from unittest.mock import Mock, patch

import pytest
import responses

from click import Group
from click.testing import CliRunner

from dnastack.cli.commands.workbench.users.commands import init_users_commands
from dnastack.client.models import ServiceEndpoint
from dnastack.client.workbench.workbench_user_service.client import WorkbenchUserClient
from dnastack.client.workbench.workbench_user_service.models import WorkbenchUser

_USER_SERVICE_URL = 'https://user-service.example.com/'


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

    @pytest.mark.parametrize('email', ['', '   ', 'alice'])
    @patch('dnastack.cli.commands.workbench.users.commands.get_user_client')
    def test_rejects_value_that_is_not_an_email_without_sending_a_request(self, mock_get_client, email):
        result = self.runner.invoke(self.group, ['register', '--email', email])

        assert result.exit_code == 2
        assert "--email" in result.stderr
        mock_get_client.assert_not_called()


class TestErrorResponses(_UsersCommandTest):
    """Tests for how both users commands report HTTP errors from the user service."""

    @pytest.mark.parametrize('method, path, args', [
        (responses.GET, 'users/alice%40example.com', ['describe', 'alice@example.com']),
        (responses.POST, 'users', ['register', '--email', 'alice@example.com']),
    ])
    @pytest.mark.parametrize('status', [400, 403, 404, 409])
    @responses.activate
    @patch('dnastack.cli.commands.workbench.users.commands.get_user_client')
    def test_reports_http_status_and_exits_non_zero(self, mock_get_client, status, method, path, args):
        mock_get_client.return_value = WorkbenchUserClient(ServiceEndpoint(
            id='test',
            url=_USER_SERVICE_URL,
            type=WorkbenchUserClient.get_default_service_type(),
        ))
        responses.add(method, f'{_USER_SERVICE_URL}{path}', status=status, body='rejected')

        result = self.runner.invoke(self.group, args)

        assert result.exit_code == 1
        assert f"HTTP {status}: rejected" in result.stderr
        assert result.stdout == ""
