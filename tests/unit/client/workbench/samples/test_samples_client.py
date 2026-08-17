from unittest.mock import MagicMock, Mock, patch

from dnastack.client.models import ServiceEndpoint
from dnastack.client.workbench.samples.client import SamplesClient
from dnastack.client.workbench.samples.models import MetadataProcessingResult


def _client_with_session(response):
    client = SamplesClient(ServiceEndpoint(id='samples', url='https://sample-service.test/'),
                           namespace='ns')
    session = MagicMock()
    session.__enter__.return_value = session
    session.post.return_value = response
    session.get.return_value = response
    return client, session


class TestUploadMetadata:
    """The service dispatches on file name and on the `override` part, so both must be exact."""

    def _upload(self, tmp_path, preserve_existing):
        response = Mock()
        response.json.return_value = {'results': []}
        client, session = _client_with_session(response)
        file = tmp_path / 'lab.attributes.json'
        file.write_text('{"HG002": {"kit_lot": "A7-2291"}}')

        with patch.object(SamplesClient, 'create_http_session', return_value=session):
            client.upload_metadata(files=[file], preserve_existing=preserve_existing)
        return session.post.call_args

    def test_overrides_existing_values_by_default(self, tmp_path):
        call = self._upload(tmp_path, preserve_existing=False)
        assert call.kwargs['data'] == {'override': (None, 'true')}

    def test_preserves_existing_values_when_asked(self, tmp_path):
        call = self._upload(tmp_path, preserve_existing=True)
        assert call.kwargs['data'] == {'override': (None, 'false')}

    def test_sends_each_file_as_a_metadata_part_under_its_own_name(self, tmp_path):
        call = self._upload(tmp_path, preserve_existing=False)
        assert call.kwargs['files'] == [
            ('metadata', ('lab.attributes.json', b'{"HG002": {"kit_lot": "A7-2291"}}'))
        ]

    def test_posts_to_the_namespaced_metadata_resource(self, tmp_path):
        call = self._upload(tmp_path, preserve_existing=False)
        assert call.args[0] == 'https://sample-service.test/ns/samples/metadata'


class TestGetSampleAttributes:

    def test_returns_the_response_text_unparsed(self):
        response = Mock()
        response.text = '{"zeta": {"nested": null}, "alpha": 1}'
        client, session = _client_with_session(response)

        with patch.object(SamplesClient, 'create_http_session', return_value=session):
            attributes = client.get_sample_attributes('HG002')

        assert attributes == '{"zeta": {"nested": null}, "alpha": 1}'
        assert session.get.call_args.args[0] == 'https://sample-service.test/ns/samples/HG002/attributes'


class TestReplaceSampleAttributes:

    def _replace(self, document):
        response = Mock()
        response.text = document
        client, session = _client_with_session(response)
        with patch.object(SamplesClient, 'create_http_session', return_value=session):
            client.replace_sample_attributes('HG002', document)
        return session.put.call_args

    def test_sends_the_document_as_given_rather_than_reserialising_it(self):
        """Re-encoding would normalise floats and drop the caller's key order."""
        document = '{"zeta": {"nested": null}, "alpha": 1.0}'
        call = self._replace(document)
        assert call.kwargs['data'] == document.encode('utf-8')

    def test_declares_a_json_content_type(self):
        call = self._replace('{}')
        assert call.kwargs['headers'] == {'Content-Type': 'application/json'}

    def test_puts_to_the_sample_attributes_resource(self):
        call = self._replace('{}')
        assert call.args[0] == 'https://sample-service.test/ns/samples/HG002/attributes'


class TestMetadataProcessingResult:

    def test_reads_the_camel_case_wire_format(self):
        """The metadata endpoint is the only sample-service resource that serialises camelCase."""
        result = MetadataProcessingResult(**{
            'fileName': 'lab.attributes.json',
            'outcome': 'SUCCESS',
            'sampleIds': ['HG002'],
            'errors': ['HG999: Sample does not exist'],
        })

        assert result.file_name == 'lab.attributes.json'
        assert result.sample_ids == ['HG002']
        assert result.errors == ['HG999: Sample does not exist']

    def test_defaults_sample_ids_to_empty_when_the_service_omits_them(self):
        assert MetadataProcessingResult(fileName='broken.json', outcome='FAILED').sample_ids == []
