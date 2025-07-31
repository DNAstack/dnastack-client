import unittest
from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
from assertpy import assert_that


class TestWorkflowUtils(unittest.TestCase):
    def test_that_none_input_returns_none(self):
        result = _get_labels_patch(None)
        assert_that(result).is_none()

    def test_remove_operation_cases(self):
        test_cases = [
            ([""], "empty string in list"),
            (["   "], "whitespace only string in list"),
            (["", "  ", "  ", ""], "all empty labels")
        ]
        
        for input_value, description in test_cases:
            with self.subTest(input_value=input_value, description=description):
                result = _get_labels_patch(input_value)
                assert_that(result).is_not_none()
                assert_that(result.path).is_equal_to("/labels")
                assert_that(result.op).is_equal_to("remove")

    def test_replace_operation_cases(self):
        test_cases = [
            (["alpha"], ["alpha"], "single label"),
            (["alpha", "beta", "gamma"], ["alpha", "beta", "gamma"], "multiple labels"),
            (["alpha ", " beta ", " gamma "], ["alpha", "beta", "gamma"], "labels with whitespace"),
            (["alpha", "", "beta", "  ", "gamma"], ["alpha", "beta", "gamma"], "empty labels filtered out"),
            (["  alpha  "], ["alpha"], "single label with spaces")
        ]
        
        for input_value, expected_labels, description in test_cases:
            with self.subTest(input_value=input_value, expected_labels=expected_labels, description=description):
                result = _get_labels_patch(input_value)
                assert_that(result).is_not_none()
                assert_that(result.path).is_equal_to("/labels")
                assert_that(result.op).is_equal_to("replace")
                assert_that(result.value).is_equal_to(expected_labels)