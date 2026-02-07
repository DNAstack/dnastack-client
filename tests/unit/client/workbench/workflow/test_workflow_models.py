"""Tests for workflow models, particularly the WorkflowSource enum."""

import pytest

from dnastack.client.workbench.workflow.models import WorkflowSource


class TestWorkflowSource:
    """Test suite for WorkflowSource enum validation."""

    def test_workflow_source_dnastack_exists(self):
        """Test that DNASTACK source is available in the enum.

        Regression test for CU-86b8ay4x0: Users could not filter by source
        'DNASTACK' because it was missing from the WorkflowSource enum.
        """
        assert hasattr(WorkflowSource, 'dnastack')
        assert WorkflowSource.dnastack.value == "DNASTACK"

    def test_workflow_source_all_expected_values(self):
        """Test that all expected workflow sources are defined."""
        expected_sources = {
            'dockstore': 'DOCKSTORE',
            'custom': 'CUSTOM',
            'private': 'PRIVATE',
            'dnastack': 'DNASTACK',
        }

        for name, value in expected_sources.items():
            assert hasattr(WorkflowSource, name), f"WorkflowSource missing '{name}'"
            assert getattr(WorkflowSource, name).value == value

    def test_workflow_source_can_be_used_as_cli_choices(self):
        """Test that WorkflowSource values can be used for CLI choices."""
        choices = [e.value for e in WorkflowSource]

        assert 'DOCKSTORE' in choices
        assert 'CUSTOM' in choices
        assert 'PRIVATE' in choices
        assert 'DNASTACK' in choices

    @pytest.mark.parametrize("source_value", [
        "DOCKSTORE",
        "CUSTOM",
        "PRIVATE",
        "DNASTACK",
    ])
    def test_workflow_source_from_value(self, source_value: str):
        """Test that WorkflowSource can be instantiated from string values."""
        source = WorkflowSource(source_value)
        assert source.value == source_value
