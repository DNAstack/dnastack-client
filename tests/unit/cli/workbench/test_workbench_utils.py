import unittest

class TestWorkflowUtils(unittest.TestCase):
    """Unit tests for workflow utilities"""

    def test_get_labels_patch_none_input(self):
        """Test that None input returns None"""
        from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
        result = _get_labels_patch(None)
        self.assertIsNone(result)

    def test_get_labels_patch_empty_string(self):
        """Test that empty string returns remove operation"""
        from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
        result = _get_labels_patch("")
        self.assertIsNotNone(result)
        self.assertEqual(result.path, "/labels")
        self.assertEqual(result.op, "remove")

    def test_get_labels_patch_whitespace_only(self):
        """Test that whitespace-only string returns remove operation"""
        from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
        result = _get_labels_patch("   ")
        self.assertIsNotNone(result)
        self.assertEqual(result.path, "/labels")
        self.assertEqual(result.op, "remove")

    def test_get_labels_patch_single_label(self):
        """Test that single label returns replace operation"""
        from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
        result = _get_labels_patch("alpha")
        self.assertIsNotNone(result)
        self.assertEqual(result.path, "/labels")
        self.assertEqual(result.op, "replace")
        self.assertEqual(result.value, ["alpha"])

    def test_get_labels_patch_multiple_labels(self):
        """Test that multiple labels returns replace operation with list"""
        from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
        result = _get_labels_patch("alpha,beta,gamma")
        self.assertIsNotNone(result)
        self.assertEqual(result.path, "/labels")
        self.assertEqual(result.op, "replace")
        self.assertEqual(result.value, ["alpha", "beta", "gamma"])

    def test_get_labels_patch_labels_with_whitespace(self):
        """Test that labels with whitespace are properly trimmed"""
        from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
        result = _get_labels_patch("alpha , beta , gamma ")
        self.assertIsNotNone(result)
        self.assertEqual(result.path, "/labels")
        self.assertEqual(result.op, "replace")
        self.assertEqual(result.value, ["alpha", "beta", "gamma"])

    def test_get_labels_patch_empty_labels_in_list(self):
        """Test that empty labels in comma-separated list are filtered out"""
        from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
        result = _get_labels_patch("alpha,,beta,  ,gamma")
        self.assertIsNotNone(result)
        self.assertEqual(result.path, "/labels")
        self.assertEqual(result.op, "replace")
        self.assertEqual(result.value, ["alpha", "beta", "gamma"])

    def test_get_labels_patch_all_empty_labels(self):
        """Test that all empty labels results in remove operation"""
        from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
        result = _get_labels_patch(",,  ,  ,")
        self.assertIsNotNone(result)
        self.assertEqual(result.path, "/labels")
        self.assertEqual(result.op, "remove")

    def test_get_labels_patch_single_label_with_spaces(self):
        """Test that single label with spaces is properly trimmed"""
        from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
        result = _get_labels_patch("  alpha  ")
        self.assertIsNotNone(result)
        self.assertEqual(result.path, "/labels")
        self.assertEqual(result.op, "replace")
        self.assertEqual(result.value, ["alpha"])