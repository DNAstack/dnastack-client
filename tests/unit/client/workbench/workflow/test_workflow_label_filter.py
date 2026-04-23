"""Tests for label filtering on workflow and version list commands.

Covers [CU-86b5yw7nc]: Allow filtering workflows by labels from the CLI.
"""
from unittest.mock import Mock, patch

from click.testing import CliRunner

from dnastack.cli.commands.workbench.workflows import workflows_command_group
from dnastack.client.workbench.workflow.models import (
    WorkflowListOptions,
    WorkflowVersion,
    WorkflowVersionListOptions,
)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestWorkflowListOptionsLabelFilter:
    def test_accepts_single_label(self):
        opts = WorkflowListOptions(label=['genomics'])
        assert opts.label == ['genomics']

    def test_accepts_multiple_labels(self):
        opts = WorkflowListOptions(label=['genomics', 'wgs'])
        assert opts.label == ['genomics', 'wgs']

    def test_label_excluded_when_none(self):
        opts = WorkflowListOptions()
        dumped = opts.model_dump(exclude_none=True)
        assert 'label' not in dumped

    def test_label_included_in_serialized_params(self):
        opts = WorkflowListOptions(label=['genomics', 'wgs'])
        dumped = opts.model_dump(exclude_none=True)
        assert dumped['label'] == ['genomics', 'wgs']


class TestWorkflowVersionListOptionsLabelFilter:
    def test_accepts_single_label(self):
        opts = WorkflowVersionListOptions(label=['v2'])
        assert opts.label == ['v2']

    def test_accepts_multiple_labels(self):
        opts = WorkflowVersionListOptions(label=['v2', 'stable'])
        assert opts.label == ['v2', 'stable']

    def test_label_excluded_when_none(self):
        opts = WorkflowVersionListOptions()
        dumped = opts.model_dump(exclude_none=True)
        assert 'label' not in dumped

    def test_label_included_in_serialized_params(self):
        opts = WorkflowVersionListOptions(label=['v2', 'stable'])
        dumped = opts.model_dump(exclude_none=True)
        assert dumped['label'] == ['v2', 'stable']


class TestWorkflowVersionLabelsField:
    def test_workflow_version_accepts_labels(self):
        version = WorkflowVersion(
            id='v1',
            versionName='1.0',
            workflowName='my-workflow',
            descriptorType='WDL',
            labels=['stable', 'production'],
        )
        assert version.labels == ['stable', 'production']

    def test_workflow_version_labels_defaults_to_none(self):
        version = WorkflowVersion(
            id='v1',
            versionName='1.0',
            workflowName='my-workflow',
            descriptorType='WDL',
        )
        assert version.labels is None


# ---------------------------------------------------------------------------
# CLI command tests
# ---------------------------------------------------------------------------

def _make_mock_client(workflows=None, versions=None):
    client = Mock()
    client.list_workflows.return_value = iter(workflows or [])
    client.list_workflow_versions.return_value = iter(versions or [])
    return client


@patch('dnastack.cli.commands.workbench.workflows.commands.get_workflow_client')
class TestListWorkflowsLabelFlag:
    def test_single_label_passed_to_list_options(self, mock_get_client):
        mock_client = _make_mock_client()
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(workflows_command_group, ['list', '--label', 'genomics'])

        assert result.exit_code == 0, result.output
        mock_client.list_workflows.assert_called_once()
        list_options = mock_client.list_workflows.call_args.kwargs['list_options']
        assert list_options.label == ['genomics']

    def test_multiple_labels_passed_to_list_options(self, mock_get_client):
        mock_client = _make_mock_client()
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(workflows_command_group, [
            'list', '--label', 'genomics', '--label', 'wgs'
        ])

        assert result.exit_code == 0, result.output
        list_options = mock_client.list_workflows.call_args.kwargs['list_options']
        assert list_options.label == ['genomics', 'wgs']

    def test_no_label_flag_sends_none(self, mock_get_client):
        mock_client = _make_mock_client()
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(workflows_command_group, ['list'])

        assert result.exit_code == 0, result.output
        list_options = mock_client.list_workflows.call_args.kwargs['list_options']
        assert list_options.label is None


@patch('dnastack.cli.commands.workbench.workflows.versions.commands.get_workflow_client')
class TestListVersionsLabelFlag:
    def test_single_label_passed_to_list_options(self, mock_get_client):
        mock_client = _make_mock_client()
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(workflows_command_group, [
            'versions', 'list', '--workflow', 'wf-123', '--label', 'stable'
        ])

        assert result.exit_code == 0, result.output
        mock_client.list_workflow_versions.assert_called_once()
        list_options = mock_client.list_workflow_versions.call_args.kwargs['list_options']
        assert list_options.label == ['stable']

    def test_multiple_labels_passed_to_list_options(self, mock_get_client):
        mock_client = _make_mock_client()
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(workflows_command_group, [
            'versions', 'list', '--workflow', 'wf-123',
            '--label', 'stable', '--label', 'v2'
        ])

        assert result.exit_code == 0, result.output
        list_options = mock_client.list_workflow_versions.call_args.kwargs['list_options']
        assert list_options.label == ['stable', 'v2']

    def test_no_label_flag_sends_none(self, mock_get_client):
        mock_client = _make_mock_client()
        mock_get_client.return_value = mock_client

        runner = CliRunner()
        result = runner.invoke(workflows_command_group, [
            'versions', 'list', '--workflow', 'wf-123'
        ])

        assert result.exit_code == 0, result.output
        list_options = mock_client.list_workflow_versions.call_args.kwargs['list_options']
        assert list_options.label is None
