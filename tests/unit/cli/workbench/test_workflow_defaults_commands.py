"""Unit tests for workflow version defaults CLI commands.

Covers [CU-86b46744d]: Add selector filter to defaults list and search commands.
"""
from unittest.mock import Mock, patch

from click.testing import CliRunner

from dnastack.cli.commands.workbench.workflows import workflows_command_group
from dnastack.client.workbench.workflow.models import WorkflowDefaultsListOptions, WorkflowDefaults


def _make_mock_client(defaults=None, search_result=None):
    client = Mock()
    client.list_workflow_defaults.return_value = iter(defaults or [])
    client.search_workflow_defaults.return_value = search_result
    return client


REQUIRED_ARGS = ['versions', 'defaults', 'list', '--workflow', 'wf-123', '--version', 'v-456']
SEARCH_REQUIRED_ARGS = ['versions', 'defaults', 'search', '--workflow', 'wf-123', '--version', 'v-456']


@patch('dnastack.cli.commands.workbench.workflows.versions.defaults.get_workflow_client')
class TestDefaultsListFilterFlags:

    def test_provider_filter_passed_to_list_options(self, mock_get_client):
        mock_get_client.return_value = _make_mock_client()
        result = CliRunner().invoke(workflows_command_group, REQUIRED_ARGS + ['--provider', 'GCP'])
        assert result.exit_code == 0, result.output
        opts = mock_get_client.return_value.list_workflow_defaults.call_args.kwargs['list_options']
        assert opts.provider == 'GCP'

    def test_region_filter_passed_to_list_options(self, mock_get_client):
        mock_get_client.return_value = _make_mock_client()
        result = CliRunner().invoke(workflows_command_group, REQUIRED_ARGS + ['--region', 'us-central1'])
        assert result.exit_code == 0, result.output
        opts = mock_get_client.return_value.list_workflow_defaults.call_args.kwargs['list_options']
        assert opts.region == 'us-central1'

    def test_engine_filter_passed_to_list_options(self, mock_get_client):
        mock_get_client.return_value = _make_mock_client()
        result = CliRunner().invoke(workflows_command_group, REQUIRED_ARGS + ['--engine', 'cromwell'])
        assert result.exit_code == 0, result.output
        opts = mock_get_client.return_value.list_workflow_defaults.call_args.kwargs['list_options']
        assert opts.engine == 'cromwell'

    def test_all_three_filters_combined(self, mock_get_client):
        mock_get_client.return_value = _make_mock_client()
        result = CliRunner().invoke(workflows_command_group,
            REQUIRED_ARGS + ['--provider', 'GCP', '--region', 'us-central1', '--engine', 'cromwell'])
        assert result.exit_code == 0, result.output
        opts = mock_get_client.return_value.list_workflow_defaults.call_args.kwargs['list_options']
        assert opts.provider == 'GCP'
        assert opts.region == 'us-central1'
        assert opts.engine == 'cromwell'

    def test_no_filters_sends_none(self, mock_get_client):
        mock_get_client.return_value = _make_mock_client()
        result = CliRunner().invoke(workflows_command_group, REQUIRED_ARGS)
        assert result.exit_code == 0, result.output
        opts = mock_get_client.return_value.list_workflow_defaults.call_args.kwargs['list_options']
        assert opts.provider is None
        assert opts.region is None
        assert opts.engine is None

    def test_filters_excluded_from_serialization_when_none(self, mock_get_client):
        mock_get_client.return_value = _make_mock_client()
        opts = WorkflowDefaultsListOptions()
        dumped = opts.model_dump(exclude_none=True)
        assert 'provider' not in dumped
        assert 'region' not in dumped
        assert 'engine' not in dumped

    def test_filters_included_in_serialization_when_set(self, mock_get_client):
        mock_get_client.return_value = _make_mock_client()
        opts = WorkflowDefaultsListOptions(provider='GCP', region='us-central1')
        dumped = opts.model_dump(exclude_none=True)
        assert dumped['provider'] == 'GCP'
        assert dumped['region'] == 'us-central1'
        assert 'engine' not in dumped


@patch('dnastack.cli.commands.workbench.workflows.versions.defaults.get_workflow_client')
class TestDefaultsSearchCommand:

    def test_search_with_provider_and_region(self, mock_get_client):
        mock_default = WorkflowDefaults(id='d1', name='test')
        mock_get_client.return_value = _make_mock_client(search_result=mock_default)
        result = CliRunner().invoke(workflows_command_group,
            SEARCH_REQUIRED_ARGS + ['--provider', 'GCP', '--region', 'us-central1'])
        assert result.exit_code == 0, result.output
        mock_get_client.return_value.search_workflow_defaults.assert_called_once_with(
            workflow_id='wf-123', version_id='v-456', engine=None, provider='GCP', region='us-central1')

    def test_search_returns_not_found_exit_code_1(self, mock_get_client):
        mock_get_client.return_value = _make_mock_client(search_result=None)
        result = CliRunner().invoke(workflows_command_group, SEARCH_REQUIRED_ARGS + ['--provider', 'GCP'])
        assert result.exit_code == 1

    def test_search_with_no_filters_calls_client(self, mock_get_client):
        mock_default = WorkflowDefaults(id='catch-all', name='catch-all')
        mock_get_client.return_value = _make_mock_client(search_result=mock_default)
        result = CliRunner().invoke(workflows_command_group, SEARCH_REQUIRED_ARGS)
        assert result.exit_code == 0, result.output
        mock_get_client.return_value.search_workflow_defaults.assert_called_once_with(
            workflow_id='wf-123', version_id='v-456', engine=None, provider=None, region=None)
