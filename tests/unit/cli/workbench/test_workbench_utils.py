import unittest
from unittest.mock import patch

import click

from dnastack.cli.commands.workbench.utils import resolve_storage_account_id
from dnastack.cli.commands.workbench.workflows.utils import _get_labels_patch
from dnastack.client.workbench.storage.models import StorageAccount
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

class TestResolveStorageAccountId(unittest.TestCase):
    @patch('dnastack.cli.commands.workbench.utils.get_storage_client')
    def test_that_explicit_storage_account_is_returned_without_lookup(self, mock_get_storage_client):
        result = resolve_storage_account_id('sa-explicit', context_name=None, namespace='ns')

        assert_that(result).is_equal_to('sa-explicit')
        mock_get_storage_client.assert_not_called()

    @patch('dnastack.cli.commands.workbench.utils.get_storage_client')
    def test_that_single_storage_account_in_namespace_is_used_by_default(self, mock_get_storage_client):
        mock_get_storage_client.return_value.list_storage_accounts.return_value = iter([StorageAccount(id='sa-only')])

        result = resolve_storage_account_id(None, context_name='ctx', namespace='ns')

        assert_that(result).is_equal_to('sa-only')
        mock_get_storage_client.assert_called_once_with(context_name='ctx', namespace='ns')

    @patch('dnastack.cli.commands.workbench.utils.get_storage_client')
    def test_that_multiple_storage_accounts_raise_error_listing_them(self, mock_get_storage_client):
        mock_get_storage_client.return_value.list_storage_accounts.return_value = iter([
            StorageAccount(id='sa-1'), StorageAccount(id='sa-2'),
        ])

        with self.assertRaises(click.ClickException) as error:
            resolve_storage_account_id(None, context_name=None, namespace='ns')

        assert_that(error.exception.message).contains('--storage-account', 'dnastack workbench storage list')

    @patch('dnastack.cli.commands.workbench.utils.get_storage_client')
    def test_that_storage_account_lookup_fetches_at_most_two_accounts(self, mock_get_storage_client):
        mock_get_storage_client.return_value.list_storage_accounts.return_value = iter([StorageAccount(id='sa-only')])

        resolve_storage_account_id(None, context_name=None, namespace='ns')

        call_args = mock_get_storage_client.return_value.list_storage_accounts.call_args
        assert_that(call_args.kwargs['max_results']).is_equal_to(2)

    @patch('dnastack.cli.commands.workbench.utils.get_storage_client')
    def test_that_no_storage_accounts_raise_error(self, mock_get_storage_client):
        mock_get_storage_client.return_value.list_storage_accounts.return_value = iter([])

        with self.assertRaises(click.ClickException) as error:
            resolve_storage_account_id(None, context_name=None, namespace='ns')

        assert_that(error.exception.message).contains('No storage accounts', 'ns')
