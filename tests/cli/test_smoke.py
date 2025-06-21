from tests.cli.base import DeprecatedPublisherCliTestCase


class TestSmoke(DeprecatedPublisherCliTestCase):
    @staticmethod
    def reuse_session() -> bool:
        return True

    @staticmethod
    def automatically_authenticate() -> bool:
        return True

    def test_happy_path(self):
        self.invoke('use', self.explorer_urls[0])

        for collection in self.simple_invoke('collections', 'list', '--endpoint-id=collection-service'):
            collection_id = collection['slugName']
            try:
                self.invoke('collections', 'tables', 'list', '--collection', collection_id, '--endpoint-id=collection-service')
                self.invoke('collections', 'query', '-c', collection_id, 'SELECT 1', '--endpoint-id=collection-service')
                self.invoke('collections', 'query', '--collection', collection_id, 'SELECT 1','--endpoint-id=collection-service')
                return
            except Exception:
                pass

        self.fail('No usable collection for the CLI smoke test')
