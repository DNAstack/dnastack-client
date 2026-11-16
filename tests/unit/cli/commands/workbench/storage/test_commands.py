import json
from unittest.mock import patch

import pytest
import responses
from click import Group
from click.testing import CliRunner

from dnastack.cli.commands.workbench.storage.commands import init_storage_commands
from dnastack.client.models import ServiceEndpoint
from dnastack.client.workbench.storage.client import StorageClient

_SAMPLE_SERVICE_URL = 'https://sample-service.example.com/'
_ACCOUNT_URL = f'{_SAMPLE_SERVICE_URL}ns-1/storage/storage-1'


def _account(indexing_status: str, last_indexed_at: str = '2026-11-15T12:00:00Z') -> dict:
    return {"id": "storage-1", "name": "instruments", "indexing_status": indexing_status,
            "last_indexed_at": last_indexed_at}


class TestReindexCommand:
    """Tests for the storage reindex CLI command, through the real HTTP session."""

    def setup_method(self):
        self.runner = CliRunner(mix_stderr=False)
        self.group = Group()
        init_storage_commands(self.group)
        self._client_patch = patch(
            'dnastack.cli.commands.workbench.storage.commands.get_storage_client',
            return_value=StorageClient.make(ServiceEndpoint(id='test', url=_SAMPLE_SERVICE_URL), 'ns-1'))
        self.mock_get_client = self._client_patch.start()

    def teardown_method(self):
        self._client_patch.stop()

    @responses.activate
    def test_starts_reindex_and_prints_the_running_account(self):
        responses.post(f'{_ACCOUNT_URL}/reindex', json=_account('RUNNING'))

        result = self.runner.invoke(self.group, ['reindex', 'storage-1', '--namespace', 'ns-1'])

        assert result.exit_code == 0, result.stderr
        self.mock_get_client.assert_called_once_with(None, None, 'ns-1')
        assert json.loads(result.stdout)["indexing_status"] == "RUNNING"
        assert [c.request.method for c in responses.calls] == ['POST']

    @pytest.mark.parametrize('status', [400, 403, 404])
    @responses.activate
    def test_reports_http_status_and_exits_non_zero(self, status):
        responses.post(f'{_ACCOUNT_URL}/reindex', status=status, body='rejected')

        result = self.runner.invoke(self.group, ['reindex', 'storage-1'])

        assert result.exit_code == 1
        assert f"HTTP {status}: rejected" in result.stderr
        assert result.stdout == ""

    def test_requires_storage_id(self):
        result = self.runner.invoke(self.group, ['reindex'])

        assert result.exit_code == 2
        self.mock_get_client.assert_not_called()

    @responses.activate
    @patch('dnastack.cli.commands.workbench.storage.commands.sleep')
    def test_wait_polls_until_indexing_finishes_and_prints_the_final_account(self, mock_sleep):
        responses.get(_ACCOUNT_URL, json=_account('IDLE'))
        responses.post(f'{_ACCOUNT_URL}/reindex', json=_account('RUNNING'))
        responses.get(_ACCOUNT_URL, json=_account('RUNNING'))
        responses.get(_ACCOUNT_URL, json=_account('IDLE', last_indexed_at='2026-11-16T09:30:00Z'))

        result = self.runner.invoke(self.group, ['reindex', 'storage-1', '--wait'])

        assert result.exit_code == 0, result.stderr
        assert [c.request.method for c in responses.calls] == ['GET', 'POST', 'GET', 'GET']
        assert mock_sleep.call_count == 2
        output = json.loads(result.stdout)
        assert output["indexing_status"] == "IDLE"
        assert output["last_indexed_at"] == "2026-11-16T09:30:00Z"

    @responses.activate
    @patch('dnastack.cli.commands.workbench.storage.commands.sleep')
    def test_wait_gives_up_after_the_timeout_and_exits_non_zero(self, mock_sleep):
        responses.get(_ACCOUNT_URL, json=_account('IDLE'))
        responses.post(f'{_ACCOUNT_URL}/reindex', json=_account('RUNNING'))

        result = self.runner.invoke(self.group, ['reindex', 'storage-1', '--wait', '--timeout', '0'])

        assert result.exit_code == 1
        assert "still running" in result.stderr
        assert result.stdout == ""
        mock_sleep.assert_not_called()

    @responses.activate
    def test_wait_fails_before_reindexing_when_workbench_does_not_report_indexing_status(self):
        responses.get(_ACCOUNT_URL, json={"id": "storage-1"})
        responses.post(f'{_ACCOUNT_URL}/reindex', json={"id": "storage-1"})

        result = self.runner.invoke(self.group, ['reindex', 'storage-1', '--wait'])

        assert result.exit_code == 1
        assert "indexing status" in result.stderr
        assert result.stdout == ""
        assert [c.request.method for c in responses.calls] == ['GET']

    @responses.activate
    def test_wait_succeeds_without_polling_when_indexing_finished_before_the_response(self):
        responses.get(_ACCOUNT_URL, json=_account('IDLE'))
        responses.post(f'{_ACCOUNT_URL}/reindex', json=_account('IDLE', last_indexed_at='2026-11-16T09:30:00Z'))

        result = self.runner.invoke(self.group, ['reindex', 'storage-1', '--wait'])

        assert result.exit_code == 0, result.stderr
        assert [c.request.method for c in responses.calls] == ['GET', 'POST']
        assert json.loads(result.stdout)["last_indexed_at"] == "2026-11-16T09:30:00Z"

    @responses.activate
    def test_rejects_timeout_without_wait(self):
        result = self.runner.invoke(self.group, ['reindex', 'storage-1', '--timeout', '60'])

        assert result.exit_code == 2
        assert len(responses.calls) == 0
        assert "--wait" in result.stderr

    @responses.activate
    @patch('dnastack.cli.commands.workbench.storage.commands.sleep')
    def test_wait_fails_when_indexing_stops_without_recording_a_completed_run(self, mock_sleep):
        responses.get(_ACCOUNT_URL, json=_account('IDLE'))
        responses.post(f'{_ACCOUNT_URL}/reindex', json=_account('RUNNING'))
        responses.get(_ACCOUNT_URL, json=_account('IDLE'))

        result = self.runner.invoke(self.group, ['reindex', 'storage-1', '--wait'])

        assert result.exit_code == 1
        assert "did not complete" in result.stderr
        assert result.stdout == ""

    @responses.activate
    def test_wait_fails_on_an_indexing_status_it_does_not_know(self):
        responses.get(_ACCOUNT_URL, json=_account('IDLE'))
        responses.post(f'{_ACCOUNT_URL}/reindex', json=_account('QUEUED', last_indexed_at='2026-11-16T09:30:00Z'))

        result = self.runner.invoke(self.group, ['reindex', 'storage-1', '--wait'])

        assert result.exit_code == 1
        assert "QUEUED" in result.stderr
        assert result.stdout == ""

    @responses.activate
    def test_wait_rejects_a_negative_timeout(self):
        result = self.runner.invoke(self.group, ['reindex', 'storage-1', '--wait', '--timeout', '-1'])

        assert result.exit_code == 2
        assert len(responses.calls) == 0
        assert "--timeout" in result.stderr
