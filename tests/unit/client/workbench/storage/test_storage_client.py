import pytest
import responses

from dnastack.client.models import ServiceEndpoint
from dnastack.client.workbench.storage.client import StorageClient
from dnastack.client.workbench.storage.models import StorageAccount

_SAMPLE_SERVICE_URL = 'https://sample-service.example.com/'


def _make_client():
    return StorageClient.make(ServiceEndpoint(id='test', url=_SAMPLE_SERVICE_URL), 'ns-1')


class TestReindexStorageAccount:
    """Tests for StorageClient.reindex_storage_account"""

    @responses.activate
    def test_posts_reindex_without_a_body_and_returns_the_running_account(self):
        responses.post(f'{_SAMPLE_SERVICE_URL}ns-1/storage/storage-1/reindex',
                       json={"id": "storage-1", "name": "instruments", "indexing_status": "RUNNING",
                             "last_indexed_at": "2026-11-15T12:00:00Z"})

        account = _make_client().reindex_storage_account('storage-1')

        assert responses.calls[0].request.body is None
        assert account.id == "storage-1"
        assert account.indexing_status == "RUNNING"
        assert account.last_indexed_at == "2026-11-15T12:00:00Z"

    @pytest.mark.parametrize('storage_account_id', ['', '.', '..'])
    def test_rejects_ids_that_cannot_be_one_path_segment(self, storage_account_id):
        with pytest.raises(ValueError):
            _make_client().reindex_storage_account(storage_account_id)


_ODD_ID = 'a/../b#c?d'
_ODD_SEGMENT = 'a%2F..%2Fb%23c%3Fd'
_ACCOUNT_JSON = {"id": _ODD_ID, "name": "instruments"}


class TestStorageAccountIdIsOnePathSegment:
    """Every StorageClient method that addresses one account sends its id as a single escaped path segment."""

    @pytest.mark.parametrize('method, call, suffix', [
        ('GET', lambda client: client.get_storage_account(_ODD_ID), ''),
        ('PUT', lambda client: client.update_storage_account(_ODD_ID, StorageAccount(), 'etag-1'), ''),
        ('DELETE', lambda client: client.delete_storage_account(_ODD_ID), ''),
        ('POST', lambda client: client.reindex_storage_account(_ODD_ID), '/reindex'),
    ])
    @responses.activate
    def test_escapes_the_id(self, method, call, suffix):
        expected_url = f'{_SAMPLE_SERVICE_URL}ns-1/storage/{_ODD_SEGMENT}{suffix}'
        responses.add(method, expected_url, json=_ACCOUNT_JSON)

        call(_make_client())

        assert responses.calls[0].request.url == expected_url

    @pytest.mark.parametrize('call', [
        lambda client: client.get_storage_account('..'),
        lambda client: client.update_storage_account('', StorageAccount(), 'etag-1'),
        lambda client: client.delete_storage_account('.'),
    ])
    def test_rejects_ids_that_cannot_be_one_path_segment(self, call):
        with pytest.raises(ValueError):
            call(_make_client())
