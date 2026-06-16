import tempfile
from unittest.mock import Mock, patch

import pytest

from dnastack.cli.commands.dataconnect.utils import handle_query


class TestHandleQueryFileInput:

    def _make_client(self):
        client = Mock()
        client.query.return_value = iter([])
        return client

    def test_inline_query_passed_through(self):
        client = self._make_client()
        with patch('dnastack.cli.commands.dataconnect.utils.show_iterator'):
            handle_query(client, 'SELECT 1', allow_using_query_from_file=True)
        client.query.assert_called_once_with('SELECT 1', no_auth=False, trace=None)

    def test_at_file_syntax_reads_file_contents(self):
        client = self._make_client()
        sql = 'SELECT * FROM my_table WHERE id = 1'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
            f.write(sql)
            f.flush()
            with patch('dnastack.cli.commands.dataconnect.utils.show_iterator'):
                handle_query(client, f'@{f.name}', allow_using_query_from_file=True)
        client.query.assert_called_once_with(sql, no_auth=False, trace=None)

    def test_at_file_syntax_raises_on_missing_file(self):
        client = self._make_client()
        with pytest.raises(IOError, match='File not found'):
            handle_query(client, '@/nonexistent/query.sql', allow_using_query_from_file=True)

    def test_at_file_syntax_ignored_when_flag_disabled(self):
        client = self._make_client()
        with patch('dnastack.cli.commands.dataconnect.utils.show_iterator'):
            handle_query(client, '@some_file.sql', allow_using_query_from_file=False)
        client.query.assert_called_once_with('@some_file.sql', no_auth=False, trace=None)
