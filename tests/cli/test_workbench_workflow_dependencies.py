from unittest import TestCase
from unittest.mock import Mock, patch
from click.testing import CliRunner

from dnastack.cli.commands.workbench.workflows.versions.dependencies.commands import dependencies
from dnastack.cli.commands.workbench.workflows.utils import WorkflowDependencyParseError, parse_workflow_dependency
from dnastack.client.workbench.workflow.models import (
    WorkflowDependency, 
    WorkflowDependencyPrerequisite
)


class TestWorkflowDependencyCommands(TestCase):
    """Unit tests for workbench workflow dependency commands"""
    
    def setUp(self):
        self.runner = CliRunner()
        self.mock_workflow_client = Mock()
        
        # Mock workflow dependency data
        self.mock_dependency = WorkflowDependency(
            namespace="test-namespace",
            id="dep-123",
            workflow_id="workflow-1",
            workflow_version_id="v1.0",
            name="test-dependency",
            dependencies=[
                WorkflowDependencyPrerequisite(
                    workflow_id="upstream-workflow",
                    workflow_version_id="v2.0"
                )
            ],
            global_=False,
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )
        
        # Mock workflow for latest version resolution
        self.mock_workflow = Mock()
        self.mock_workflow.latestVersion = "v2.0"
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_create_dependency_single(self, mock_get_client):
        """Test creating a single workflow dependency"""
        mock_get_client.return_value = self.mock_workflow_client
        self.mock_workflow_client.create_workflow_dependency.return_value = self.mock_dependency
        self.mock_workflow_client.get_workflow.return_value = self.mock_workflow
        
        result = self.runner.invoke(dependencies, [
            'create',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--name', 'test-dependency',
            '--dependency', 'upstream-workflow/v2.0'
        ])
        
        self.assertEqual(result.exit_code, 0)
        self.mock_workflow_client.create_workflow_dependency.assert_called_once()
        
        # Verify the request was created correctly
        call_args = self.mock_workflow_client.create_workflow_dependency.call_args
        self.assertEqual(call_args[1]['workflow_id'], 'workflow-1')
        self.assertEqual(call_args[1]['workflow_version_id'], 'v1.0')
        self.assertFalse(call_args[1]['admin_only_action'])
        
        create_request = call_args[1]['workflow_dependency_create_request']
        self.assertEqual(create_request.name, 'test-dependency')
        self.assertEqual(len(create_request.dependencies), 1)
        self.assertEqual(create_request.dependencies[0].workflow_id, 'upstream-workflow')
        self.assertEqual(create_request.dependencies[0].workflow_version_id, 'v2.0')
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_create_dependency_multiple(self, mock_get_client):
        """Test creating multiple workflow dependencies"""
        mock_get_client.return_value = self.mock_workflow_client
        self.mock_workflow_client.create_workflow_dependency.return_value = self.mock_dependency
        self.mock_workflow_client.get_workflow.return_value = self.mock_workflow
        
        result = self.runner.invoke(dependencies, [
            'create',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--name', 'test-dependency',
            '--dependency', 'upstream-workflow/v2.0',
            '--dependency', 'another-workflow/v1.5'
        ])
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify the request was created with multiple dependencies
        call_args = self.mock_workflow_client.create_workflow_dependency.call_args
        create_request = call_args[1]['workflow_dependency_create_request']
        self.assertEqual(len(create_request.dependencies), 2)
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_create_dependency_with_latest_version(self, mock_get_client):
        """Test creating dependency with latest version resolution"""
        mock_get_client.return_value = self.mock_workflow_client
        self.mock_workflow_client.create_workflow_dependency.return_value = self.mock_dependency
        self.mock_workflow_client.get_workflow.return_value = self.mock_workflow
        
        result = self.runner.invoke(dependencies, [
            'create',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--name', 'test-dependency',
            '--dependency', 'upstream-workflow'  # No version specified
        ])
        
        self.assertEqual(result.exit_code, 0)
        self.mock_workflow_client.get_workflow.assert_called_with('upstream-workflow')
        
        # Verify the dependency was resolved to the latest version
        call_args = self.mock_workflow_client.create_workflow_dependency.call_args
        create_request = call_args[1]['workflow_dependency_create_request']
        self.assertEqual(create_request.dependencies[0].workflow_version_id, 'v2.0')
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_create_dependency_global_flag(self, mock_get_client):
        """Test creating dependency with global flag"""
        mock_get_client.return_value = self.mock_workflow_client
        self.mock_workflow_client.create_workflow_dependency.return_value = self.mock_dependency
        self.mock_workflow_client.get_workflow.return_value = self.mock_workflow
        
        result = self.runner.invoke(dependencies, [
            'create',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--name', 'test-dependency',
            '--dependency', 'upstream-workflow/v2.0',
            '--global'
        ])
        
        if result.exit_code != 0:
            print(f"Test failed with exit code {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify the global flag was passed correctly
        call_args = self.mock_workflow_client.create_workflow_dependency.call_args
        self.assertTrue(call_args[1]['admin_only_action'])
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_list_dependencies(self, mock_get_client):
        """Test listing workflow dependencies"""
        mock_get_client.return_value = self.mock_workflow_client
        mock_iterator = [self.mock_dependency]
        self.mock_workflow_client.list_workflow_dependencies.return_value = mock_iterator
        
        result = self.runner.invoke(dependencies, [
            'list',
            '--workflow', 'workflow-1',
            '--version', 'v1.0'
        ])
        
        self.assertEqual(result.exit_code, 0)
        self.mock_workflow_client.list_workflow_dependencies.assert_called_once()
        
        # Verify the parameters were passed correctly
        call_args = self.mock_workflow_client.list_workflow_dependencies.call_args
        self.assertEqual(call_args[1]['workflow_id'], 'workflow-1')
        self.assertEqual(call_args[1]['workflow_version_id'], 'v1.0')
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_list_dependencies_with_pagination(self, mock_get_client):
        """Test listing workflow dependencies with pagination"""
        mock_get_client.return_value = self.mock_workflow_client
        mock_iterator = [self.mock_dependency]
        self.mock_workflow_client.list_workflow_dependencies.return_value = mock_iterator
        
        result = self.runner.invoke(dependencies, [
            'list',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--page', '1',
            '--page-size', '10',
            '--max-results', '50'
        ])
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify pagination parameters
        call_args = self.mock_workflow_client.list_workflow_dependencies.call_args
        self.assertEqual(call_args[1]['max_results'], 50)
        list_options = call_args[1]['list_options']
        self.assertEqual(list_options.page, 1)
        self.assertEqual(list_options.page_size, 10)
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_describe_dependency_single(self, mock_get_client):
        """Test describing a single workflow dependency"""
        mock_get_client.return_value = self.mock_workflow_client
        self.mock_workflow_client.get_workflow_dependency.return_value = self.mock_dependency
        
        result = self.runner.invoke(dependencies, [
            'describe',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            'dep-123'
        ])
        
        if result.exit_code != 0:
            print(f"Test failed with exit code {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        
        self.assertEqual(result.exit_code, 0)
        self.mock_workflow_client.get_workflow_dependency.assert_called_once_with(
            workflow_id='workflow-1',
            workflow_version_id='v1.0',
            dependency_id='dep-123'
        )
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_describe_dependency_multiple(self, mock_get_client):
        """Test describing multiple workflow dependencies"""
        mock_get_client.return_value = self.mock_workflow_client
        self.mock_workflow_client.get_workflow_dependency.return_value = self.mock_dependency
        
        result = self.runner.invoke(dependencies, [
            'describe',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            'dep-123',
            'dep-456'
        ])
        
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(self.mock_workflow_client.get_workflow_dependency.call_count, 2)
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_update_dependency(self, mock_get_client):
        """Test updating a workflow dependency"""
        mock_get_client.return_value = self.mock_workflow_client
        self.mock_workflow_client.update_workflow_dependency.return_value = self.mock_dependency
        self.mock_workflow_client.get_workflow.return_value = self.mock_workflow
        
        result = self.runner.invoke(dependencies, [
            'update',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--name', 'updated-dependency',
            '--dependency', 'new-workflow/v3.0',
            'dep-123'
        ])
        
        self.assertEqual(result.exit_code, 0)
        self.mock_workflow_client.update_workflow_dependency.assert_called_once()
        
        # Verify the update request
        call_args = self.mock_workflow_client.update_workflow_dependency.call_args
        self.assertEqual(call_args[1]['workflow_id'], 'workflow-1')
        self.assertEqual(call_args[1]['workflow_version_id'], 'v1.0')
        self.assertEqual(call_args[1]['dependency_id'], 'dep-123')
        
        update_request = call_args[1]['workflow_dependency_update_request']
        self.assertEqual(update_request.name, 'updated-dependency')
        self.assertEqual(len(update_request.dependencies), 1)
        self.assertFalse(call_args[1]['admin_only_action'])
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_update_dependency_global_flag(self, mock_get_client):
        """Test updating a workflow dependency with global flag"""
        mock_get_client.return_value = self.mock_workflow_client
        self.mock_workflow_client.update_workflow_dependency.return_value = self.mock_dependency
        self.mock_workflow_client.get_workflow.return_value = self.mock_workflow
        
        result = self.runner.invoke(dependencies, [
            'update',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--name', 'updated-dependency',
            '--dependency', 'new-workflow/v3.0',
            '--global',
            'dep-123'
        ])
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify the global flag was passed correctly
        call_args = self.mock_workflow_client.update_workflow_dependency.call_args
        self.assertTrue(call_args[1]['admin_only_action'])
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_delete_dependency_with_confirmation(self, mock_get_client):
        """Test deleting a workflow dependency with confirmation"""
        mock_get_client.return_value = self.mock_workflow_client
        
        result = self.runner.invoke(dependencies, [
            'delete',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            'dep-123',
            '--force'  # Skip confirmation
        ])
        
        self.assertEqual(result.exit_code, 0)
        self.mock_workflow_client.delete_workflow_dependency.assert_called_once_with(
            workflow_id='workflow-1',
            workflow_version_id='v1.0',
            dependency_id='dep-123',
            admin_only_action=None
        )
        
    @patch('dnastack.cli.commands.workbench.workflows.versions.dependencies.commands.get_workflow_client')
    def test_delete_dependency_global_flag(self, mock_get_client):
        """Test deleting a workflow dependency with global flag"""
        mock_get_client.return_value = self.mock_workflow_client
        
        result = self.runner.invoke(dependencies, [
            'delete',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--global',
            '--force',
            'dep-123'
        ])
        
        self.assertEqual(result.exit_code, 0)
        
        # Verify the global flag was passed correctly
        call_args = self.mock_workflow_client.delete_workflow_dependency.call_args
        self.assertTrue(call_args[1]['admin_only_action'])
        
    def test_missing_required_flags(self):
        """Test that missing required flags result in errors"""
        # Test missing workflow flag
        result = self.runner.invoke(dependencies, [
            'create',
            '--version', 'v1.0',
            '--name', 'test-dependency',
            '--dependency', 'upstream-workflow/v2.0'
        ])
        self.assertNotEqual(result.exit_code, 0)
        
        # Test missing version flag
        result = self.runner.invoke(dependencies, [
            'create',
            '--workflow', 'workflow-1',
            '--name', 'test-dependency',
            '--dependency', 'upstream-workflow/v2.0'
        ])
        self.assertNotEqual(result.exit_code, 0)
        
        # Test missing name flag
        result = self.runner.invoke(dependencies, [
            'create',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--dependency', 'upstream-workflow/v2.0'
        ])
        self.assertNotEqual(result.exit_code, 0)
        
        # Test missing dependency flag
        result = self.runner.invoke(dependencies, [
            'create',
            '--workflow', 'workflow-1',
            '--version', 'v1.0',
            '--name', 'test-dependency'
        ])
        self.assertNotEqual(result.exit_code, 0)


class TestWorkflowDependencyParsing(TestCase):
    """Unit tests for workflow dependency parsing utility functions"""
    
    def test_parse_workflow_dependency_with_version(self):
        """Test parsing workflow dependency with version"""
        workflow_id, version_id = parse_workflow_dependency("workflow-1/v1.0")
        self.assertEqual(workflow_id, "workflow-1")
        self.assertEqual(version_id, "v1.0")
        
    def test_parse_workflow_dependency_without_version(self):
        """Test parsing workflow dependency without version"""
        workflow_id, version_id = parse_workflow_dependency("workflow-1")
        self.assertEqual(workflow_id, "workflow-1")
        self.assertIsNone(version_id)
        
    def test_parse_workflow_dependency_invalid_formats(self):
        """Test parsing invalid workflow dependency formats"""
        invalid_formats = [
            "",
            "   ",
            "/workflow-1",
            "workflow-1/",
            "workflow-1//v1.0",
            "workflow-1/v1.0/extra",
            "workflow-1/",
            "/v1.0"
        ]
        
        for invalid_format in invalid_formats:
            with self.assertRaises(WorkflowDependencyParseError):
                parse_workflow_dependency(invalid_format)
                
    def test_parse_workflow_dependency_edge_cases(self):
        """Test parsing workflow dependency edge cases"""
        # Test with spaces (should be stripped)
        workflow_id, version_id = parse_workflow_dependency("  workflow-1/v1.0  ")
        self.assertEqual(workflow_id, "workflow-1")
        self.assertEqual(version_id, "v1.0")
        
        # Test with complex IDs
        workflow_id, version_id = parse_workflow_dependency("complex-workflow-name/v1.0-beta")
        self.assertEqual(workflow_id, "complex-workflow-name")
        self.assertEqual(version_id, "v1.0-beta")