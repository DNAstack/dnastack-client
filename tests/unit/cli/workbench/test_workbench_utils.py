import unittest
from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
from assertpy import assert_that

class TestWorkflowUtils(unittest.TestCase):
    def test_that_none_input_returns_none(self):
        result = _get_labels_patch(None)
        assert_that(result).is_none()

    def test_that_empty_string_returns_remove_operation(self):
        result = _get_labels_patch("")
        assert_that(result).is_not_none()
        assert_that(result.path).is_equal_to("/labels")
        assert_that(result.op).is_equal_to("remove")

    def test_that_whitespace_only_string_returns_remove_operation(self):
        result = _get_labels_patch("   ")
        assert_that(result).is_not_none()
        assert_that(result.path).is_equal_to("/labels")
        assert_that(result.op).is_equal_to("remove")

    def test_that_single_label_returns_replace_operation(self):
        result = _get_labels_patch("alpha")
        assert_that(result).is_not_none()
        assert_that(result.path).is_equal_to("/labels")
        assert_that(result.op).is_equal_to("replace")
        assert_that(result.value).is_equal_to(["alpha"])

    def test_that_multiple_labels_returns_replace_operation_with_a_list(self):
        result = _get_labels_patch("alpha,beta,gamma")
        assert_that(result).is_not_none()
        assert_that(result.path).is_equal_to("/labels")
        assert_that(result.op).is_equal_to("replace")
        assert_that(result.value).is_equal_to(["alpha", "beta", "gamma"])

    def test_that_labels_with_whitespace_are_properly_trimmed(self):
        result = _get_labels_patch("alpha , beta , gamma ")
        assert_that(result).is_not_none()
        assert_that(result.path).is_equal_to("/labels")
        assert_that(result.op).is_equal_to("replace")
        assert_that(result.value).is_equal_to(["alpha", "beta", "gamma"])

    def test_that_empty_labels_in_a_comma_separated_list_are_filtered_out(self):
        result = _get_labels_patch("alpha,,beta,  ,gamma")
        assert_that(result).is_not_none()
        assert_that(result.path).is_equal_to("/labels")
        assert_that(result.op).is_equal_to("replace")
        assert_that(result.value).is_equal_to(["alpha", "beta", "gamma"])

    def test_that_all_empty_labels_results_in_remove_operation(self):
        result = _get_labels_patch(",,  ,  ,")
        assert_that(result).is_not_none()
        assert_that(result.path).is_equal_to("/labels")
        assert_that(result.op).is_equal_to("remove")

    def test_that_single_label_with_spaces_is_properly_trimmed(self):
        result = _get_labels_patch("  alpha  ")
        assert_that(result).is_not_none()
        assert_that(result.path).is_equal_to("/labels")
        assert_that(result.op).is_equal_to("replace")
        assert_that(result.value).is_equal_to(["alpha"])