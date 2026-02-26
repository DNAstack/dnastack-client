from unittest.mock import MagicMock

import click
import pytest

from dnastack.cli.commands.workbench.namespaces.members.commands import (
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
