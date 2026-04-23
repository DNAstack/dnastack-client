"""Unit tests for workbench workflows and versions list commands.

Covers [CU-86b5yw7nc]: --label filter flag on workflows list and versions list.
"""
import unittest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from click import Group

from dnastack.cli.commands.workbench.workflows.commands import init_workflows_commands
from dnastack.cli.commands.workbench.workflows.versions.commands import init_workflows_versions_commands
from dnastack.client.workbench.workflow.models import WorkflowListOptions, WorkflowVersionListOptions


class TestWorkflowsListCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.mock_client = Mock()
        self.mock_client.list_workflows.return_value = iter([])
        self.group = Group()
        init_workflows_commands(self.group)

    @patch('dnastack.cli.commands.workbench.workflows.commands.get_workflow_client')
    def test_list_with_single_label_filter(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        result = self.runner.invoke(self.group, ['list', '--label', 'genomics'])

        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.mock_client.list_workflows.call_args.kwargs
        self.assertIsInstance(call_kwargs['list_options'], WorkflowListOptions)
        self.assertEqual(call_kwargs['list_options'].label, ['genomics'])

    @patch('dnastack.cli.commands.workbench.workflows.commands.get_workflow_client')
    def test_list_with_multiple_label_filters(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        result = self.runner.invoke(self.group, ['list', '--label', 'genomics', '--label', 'wgs'])

        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.mock_client.list_workflows.call_args.kwargs
        self.assertEqual(call_kwargs['list_options'].label, ['genomics', 'wgs'])

    @patch('dnastack.cli.commands.workbench.workflows.commands.get_workflow_client')
    def test_list_without_label_filter_sends_none(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        result = self.runner.invoke(self.group, ['list'])

        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.mock_client.list_workflows.call_args.kwargs
        self.assertIsNone(call_kwargs['list_options'].label)

    @patch('dnastack.cli.commands.workbench.workflows.commands.get_workflow_client')
    def test_list_label_filter_combined_with_search(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        result = self.runner.invoke(self.group, ['list', '--label', 'wgs', '--search', 'align'])

        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.mock_client.list_workflows.call_args.kwargs
        opts = call_kwargs['list_options']
        self.assertEqual(opts.label, ['wgs'])
        self.assertEqual(opts.search, 'align')


class TestWorkflowVersionsListCommand(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.mock_client = Mock()
        self.mock_client.list_workflow_versions.return_value = iter([])
        self.group = Group()
        init_workflows_versions_commands(self.group)

    @patch('dnastack.cli.commands.workbench.workflows.versions.commands.get_workflow_client')
    def test_list_with_single_label_filter(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        result = self.runner.invoke(self.group, ['list', '--workflow', 'wf-123', '--label', 'stable'])

        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.mock_client.list_workflow_versions.call_args.kwargs
        self.assertIsInstance(call_kwargs['list_options'], WorkflowVersionListOptions)
        self.assertEqual(call_kwargs['list_options'].label, ['stable'])

    @patch('dnastack.cli.commands.workbench.workflows.versions.commands.get_workflow_client')
    def test_list_with_multiple_label_filters(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        result = self.runner.invoke(self.group, ['list', '--workflow', 'wf-123', '--label', 'stable', '--label', 'v2'])

        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.mock_client.list_workflow_versions.call_args.kwargs
        self.assertEqual(call_kwargs['list_options'].label, ['stable', 'v2'])

    @patch('dnastack.cli.commands.workbench.workflows.versions.commands.get_workflow_client')
    def test_list_without_label_filter_sends_none(self, mock_get_client):
        mock_get_client.return_value = self.mock_client

        result = self.runner.invoke(self.group, ['list', '--workflow', 'wf-123'])

        self.assertEqual(result.exit_code, 0)
        call_kwargs = self.mock_client.list_workflow_versions.call_args.kwargs
        self.assertIsNone(call_kwargs['list_options'].label)


if __name__ == '__main__':
    unittest.main()
