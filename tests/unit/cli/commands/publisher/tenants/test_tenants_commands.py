import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from click import Group
from click.testing import CliRunner

from dnastack.cli.commands.publisher.tenants.commands import init_tenants_commands
from dnastack.client.tenants.client import UnknownTenantError
from dnastack.client.tenants.models import Tenant, TenantStatus

TENANT_ID = '6f1c1f7e-9a59-4d0c-9a8e-3b6f0f7d6a11'
UUID_LIKE_NAME = '0123456789abcdef0123456789abcdef'
GET_CLIENT = 'dnastack.cli.commands.publisher.tenants.commands._get_tenant_client'


class TenantCommandsTest:
    def setup_method(self):
        self.runner = CliRunner()
        self.group = Group()
        init_tenants_commands(self.group)
        self.client = Mock()
        self.client.list_tenants.return_value = [Tenant(id=TENANT_ID, name='sickkids', status=TenantStatus.ENABLED)]
        self.client.get_tenant.return_value = Tenant(id=TENANT_ID, name='sickkids', status=TenantStatus.ENABLED)


@patch(GET_CLIENT)
class TestCreateCommand(TenantCommandsTest):
    def test_creates_tenant_without_expiry(self, mock_get_client):
        mock_get_client.return_value = self.client
        self.client.create_tenant.return_value = Tenant(id=TENANT_ID, name='sickkids', status=TenantStatus.ENABLED)

        result = self.runner.invoke(self.group, ['create', '--name', 'sickkids'])

        assert result.exit_code == 0, result.output
        self.client.create_tenant.assert_called_once_with('sickkids', expires_at=None)
        assert json.loads(result.output)['id'] == TENANT_ID

    def test_creates_tenant_expiring_at_end_of_given_day(self, mock_get_client):
        mock_get_client.return_value = self.client
        self.client.create_tenant.return_value = Tenant(id=TENANT_ID, name='sickkids')

        with patch('dnastack.cli.commands.publisher.tenants.commands.parse_point_in_time') as parse:
            parse.return_value = datetime(2026, 11, 2, 5, tzinfo=timezone.utc)
            result = self.runner.invoke(self.group, ['create', '--name', 'sickkids', '--expires', '2026-11-01'])

        assert result.exit_code == 0, result.output
        parse.assert_called_once_with('2026-11-01')
        self.client.create_tenant.assert_called_once_with(
            'sickkids', expires_at=datetime(2026, 11, 2, 5, tzinfo=timezone.utc))

    def test_rejects_unparseable_expiry_before_calling_wallet(self, mock_get_client):
        result = self.runner.invoke(self.group, ['create', '--name', 'sickkids', '--expires', 'soon'])

        assert result.exit_code != 0
        assert 'not an ISO 8601 duration' in result.output
        mock_get_client.assert_not_called()


@patch(GET_CLIENT)
class TestDeleteCommand(TenantCommandsTest):
    def test_deletes_tenant_by_name_with_force(self, mock_get_client):
        mock_get_client.return_value = self.client

        result = self.runner.invoke(self.group, ['delete', 'sickkids', '--force'])

        assert result.exit_code == 0, result.output
        self.client.delete_tenant.assert_called_once_with(TENANT_ID)

    def test_does_not_delete_when_confirmation_declined(self, mock_get_client):
        mock_get_client.return_value = self.client

        result = self.runner.invoke(self.group, ['delete', TENANT_ID], input='n\n')

        assert result.exit_code == 0, result.output
        self.client.delete_tenant.assert_not_called()

    def test_deletes_by_id_without_looking_up_name(self, mock_get_client):
        mock_get_client.return_value = self.client

        result = self.runner.invoke(self.group, ['delete', TENANT_ID], input='y\n')

        assert result.exit_code == 0, result.output
        self.client.list_tenants.assert_not_called()
        self.client.delete_tenant.assert_called_once_with(TENANT_ID)

    def test_deletes_tenant_whose_name_parses_as_uuid_by_name(self, mock_get_client):
        mock_get_client.return_value = self.client
        self.client.get_tenant.side_effect = UnknownTenantError(UUID_LIKE_NAME)
        self.client.list_tenants.return_value = [Tenant(id=TENANT_ID, name=UUID_LIKE_NAME)]

        result = self.runner.invoke(self.group, ['delete', UUID_LIKE_NAME, '--force'])

        assert result.exit_code == 0, result.output
        self.client.delete_tenant.assert_called_once_with(TENANT_ID)

    def test_fails_for_unknown_tenant_name(self, mock_get_client):
        mock_get_client.return_value = self.client

        result = self.runner.invoke(self.group, ['delete', 'nobody', '--force'])

        assert result.exit_code != 0
        self.client.delete_tenant.assert_not_called()


@patch(GET_CLIENT)
class TestStatusCommands(TenantCommandsTest):
    def test_disable_sets_disabled_status(self, mock_get_client):
        mock_get_client.return_value = self.client

        result = self.runner.invoke(self.group, ['disable', 'sickkids'])

        assert result.exit_code == 0, result.output
        self.client.set_tenant_status.assert_called_once_with(TENANT_ID, TenantStatus.DISABLED)
        assert result.output.strip() == 'Tenant sickkids disabled'

    def test_enable_sets_enabled_status(self, mock_get_client):
        mock_get_client.return_value = self.client

        result = self.runner.invoke(self.group, ['enable', 'sickkids'])

        assert result.exit_code == 0, result.output
        self.client.set_tenant_status.assert_called_once_with(TENANT_ID, TenantStatus.ENABLED)


@patch(GET_CLIENT)
class TestExpirationCommands(TenantCommandsTest):
    def test_set_expiration_sends_parsed_expiry(self, mock_get_client):
        mock_get_client.return_value = self.client

        result = self.runner.invoke(self.group, ['set-expiration', 'sickkids', '2026-11-01T17:00:00Z'])

        assert result.exit_code == 0, result.output
        self.client.set_tenant_expiration.assert_called_once_with(
            TENANT_ID, datetime(2026, 11, 1, 17, tzinfo=timezone.utc))
        assert result.output.strip() == 'Tenant sickkids expires at 2026-11-01T17:00:00+00:00'

    def test_set_expiration_rejects_unparseable_expiry_before_calling_wallet(self, mock_get_client):
        result = self.runner.invoke(self.group, ['set-expiration', 'sickkids', 'PT1D'])

        assert result.exit_code != 0
        assert 'Invalid ISO 8601 duration' in result.output
        mock_get_client.assert_not_called()

    def test_set_expiration_requires_expiry(self, mock_get_client):
        result = self.runner.invoke(self.group, ['set-expiration', 'sickkids'])

        assert result.exit_code != 0
        mock_get_client.assert_not_called()

    def test_clear_expiration_sends_no_expiry(self, mock_get_client):
        mock_get_client.return_value = self.client

        result = self.runner.invoke(self.group, ['clear-expiration', 'sickkids'])

        assert result.exit_code == 0, result.output
        self.client.set_tenant_expiration.assert_called_once_with(TENANT_ID, None)
        assert result.output.strip() == 'Tenant sickkids no longer expires'


@patch(GET_CLIENT)
class TestReadCommands(TenantCommandsTest):
    def test_list_outputs_tenants(self, mock_get_client):
        mock_get_client.return_value = self.client

        result = self.runner.invoke(self.group, ['list'])

        assert result.exit_code == 0, result.output
        assert [t['name'] for t in json.loads(result.output)] == ['sickkids']

    def test_describe_outputs_tenant(self, mock_get_client):
        mock_get_client.return_value = self.client
        self.client.get_tenant.return_value = Tenant(id=TENANT_ID, name='sickkids', status=TenantStatus.DISABLED,
                                                     expires_at=datetime(2026, 11, 2, 5, tzinfo=timezone.utc))

        result = self.runner.invoke(self.group, ['describe', 'sickkids'])

        assert result.exit_code == 0, result.output
        self.client.get_tenant.assert_called_once_with(TENANT_ID)
        output = json.loads(result.output)
        assert output['status'] == 'DISABLED'
        assert output['expires_at'].startswith('2026-11-02')
