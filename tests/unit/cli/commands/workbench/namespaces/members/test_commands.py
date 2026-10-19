from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from dnastack.cli.commands.workbench.namespaces.members.commands import (
    init_members_commands,
    resolve_namespace,
    _validate_email_or_id,
)


class TestResolveNamespace:
    """Test suite for resolve_namespace helper."""

    def test_returns_provided_namespace(self):
        client = MagicMock()
        result = resolve_namespace(client, "my-namespace")
        assert result == "my-namespace"
        client.get_user_config.assert_not_called()

    def test_falls_back_to_default_namespace(self):
        client = MagicMock()
        client.get_user_config.return_value.default_namespace = "default-ns"
        result = resolve_namespace(client, None)
        assert result == "default-ns"
        client.get_user_config.assert_called_once()


class TestValidateEmailOrId:
    """Test suite for _validate_email_or_id validation."""

    def test_accepts_email_only(self):
        _validate_email_or_id(email="foo@dnastack.com", user_id=None)

    def test_accepts_id_only(self):
        _validate_email_or_id(email=None, user_id="abc-123")

    def test_rejects_both(self):
        with pytest.raises(click.UsageError, match="not both"):
            _validate_email_or_id(email="foo@dnastack.com", user_id="abc-123")

    def test_rejects_neither(self):
        with pytest.raises(click.UsageError, match="--email or --id"):
            _validate_email_or_id(email=None, user_id=None)


class TestAddMemberUsageErrors:
    """The email/id check is reported as a usage error, before any client is made."""

    @pytest.mark.parametrize('args, message', [
        (['add', '--role', 'ADMIN'], 'Error: Specify either --email or --id.'),
        (['add', '--role', 'ADMIN', '--email', 'foo@dnastack.com', '--id', 'abc-123'],
         'Error: Specify either --email or --id, not both.'),
    ])
    def test_add_reports_usage_error(self, args, message):
        group = click.Group()
        init_members_commands(group)
        with patch('dnastack.cli.commands.workbench.namespaces.members.commands.get_user_client') as get_client:
            result = CliRunner(mix_stderr=False).invoke(group, args)
        assert result.exit_code == 2
        assert 'Usage:' in result.stderr
        assert message in result.stderr
        get_client.assert_not_called()
