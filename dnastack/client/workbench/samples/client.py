from pathlib import Path
from typing import List, Iterator, Optional
from urllib.parse import urljoin

from dnastack.client.models import ServiceEndpoint
from dnastack.client.result_iterator import ResultIterator
from dnastack.client.service_registry.models import ServiceType
from dnastack.client.workbench.base_client import BaseWorkbenchClient, WorkbenchResultLoader
from dnastack.client.workbench.samples.models import SampleListOptions, SampleListResponse, Sample, \
    SampleFilesListOptions, SampleFileListResponse, InstrumentListResponse, InstrumentListOptions, \
    MetadataProcessingResponse
from dnastack.common.tracing import Span
from dnastack.http.session import HttpSession


class SampleListResultLoader(WorkbenchResultLoader):

    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Span,
                 list_options: Optional[SampleListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> SampleListOptions:
        return SampleListOptions()

    def extract_api_response(self, response_body: dict) -> SampleListResponse:
        return SampleListResponse(**response_body)


class SampleFilesListResultLoader(WorkbenchResultLoader):

    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Span,
                 list_options: Optional[SampleFilesListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> SampleFilesListOptions:
        return SampleFilesListOptions()

    def extract_api_response(self, response_body: dict) -> SampleFileListResponse:
        return SampleFileListResponse(**response_body)


class InstrumentListResultLoader(WorkbenchResultLoader):

    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Span,
                 list_options: Optional[InstrumentListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> InstrumentListOptions:
        return InstrumentListOptions()

    def extract_api_response(self, response_body: dict) -> InstrumentListResponse:
        return InstrumentListResponse(**response_body)


class SamplesClient(BaseWorkbenchClient):

    @staticmethod
    def get_adapter_type() -> str:
        return 'sample-service'

    @staticmethod
    def get_supported_service_types() -> List[ServiceType]:
        return [
            ServiceType(group='com.dnastack.workbench', artifact='sample-service', version='1.0.0'),
        ]

    @classmethod
    def make(cls, endpoint: ServiceEndpoint, namespace: str):
        """Create this class with the given `endpoint` and `namespace`."""
        if not endpoint.type:
            endpoint.type = cls.get_default_service_type()
        return cls(endpoint, namespace)

    def list_samples(self,
                     list_options: Optional[SampleListOptions] = None,
                     max_results: int = None,
                     trace: Optional[Span] = None
                     ) -> Iterator[Sample]:
        trace = trace or Span(origin=self)
        return ResultIterator(SampleListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/samples'),
            http_session=self.create_http_session(),
            list_options=list_options,
            max_results=max_results,
            trace=trace
        ))

    def get_sample(self, sample_id: str, trace: Optional[Span] = None) -> Sample:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(urljoin(self.endpoint.url, f'{self.namespace}/samples/{sample_id}'),
                                   trace_context=trace)
            return Sample(**response.json())

    def list_sample_files(self,
                          sample_id: str,
                          list_options: Optional[SampleFilesListOptions] = None,
                          max_results: Optional[int] = None,
                          trace: Optional[Span] = None
                          ) -> Iterator[SampleFileListResponse]:
        trace = trace or Span(origin=self)
        return ResultIterator(SampleFilesListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/samples/{sample_id}/files'),
            http_session=self.create_http_session(),
            list_options=list_options,
            max_results=max_results,
            trace=trace
        ))

    def upload_metadata(self,
                        files: List[Path],
                        preserve_existing: bool = False,
                        trace: Optional[Span] = None
                        ) -> MetadataProcessingResponse:
        """
        Upload metadata files and return one result per file.

        Each file's name determines how the service reads it, so the name is sent exactly as given:
        `*.ped` as a pedigree, `*.attributes.json` as custom attributes keyed by sample id,
        `*.json` and `*.jsonl` as phenopackets, and `*.zip` as an archive of any of those.

        An attributes document replaces each named sample's attributes outright, whatever
        `preserve_existing` is set to.

        With `preserve_existing`, a pedigree or phenopacket fills only the fields a sample does not
        already have and adds its phenotypes to the sample's existing ones. By default the file's
        values replace existing sex, affected status, family and parentage, and replace phenotypes.
        """
        trace = trace or Span(origin=self)
        # The service treats a missing part as override=false, which preserves existing values.
        data = {'override': (None, 'false' if preserve_existing else 'true')}
        parts = [('metadata', (file.name, file.read_bytes())) for file in files]
        with self.create_http_session() as session:
            response = session.post(urljoin(self.endpoint.url, f'{self.namespace}/samples/metadata'),
                                    data=data,
                                    files=parts,
                                    trace_context=trace)
            return MetadataProcessingResponse(**response.json())

    def get_sample_attributes(self, sample_id: str, trace: Optional[Span] = None) -> str:
        """
        Return the sample's attributes as the service stored them. The response text is returned
        unparsed so nulls and key order survive.
        """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url, f'{self.namespace}/samples/{sample_id}/attributes'),
                trace_context=trace)
            return response.text

    def replace_sample_attributes(self, sample_id: str, attributes: str,
                                  trace: Optional[Span] = None) -> str:
        """
        Replace the sample's attributes with `attributes`, a JSON object, and return what the
        service stored. Attributes the object omits are deleted; an empty object clears the sample.

        The text is sent as given rather than re-serialised, so values keep the types and precision
        the caller wrote.
        """
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.put(
                urljoin(self.endpoint.url, f'{self.namespace}/samples/{sample_id}/attributes'),
                data=attributes.encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                trace_context=trace)
            return response.text

    def list_instruments(self,
                         list_options: Optional[InstrumentListOptions] = None,
                         max_results: Optional[int] = None,
                         trace: Optional[Span] = None
                         ) -> Iterator[InstrumentListResponse]:
        trace = trace or Span(origin=self)
        return ResultIterator(InstrumentListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/instruments'),
            http_session=self.create_http_session(),
            list_options=list_options,
            max_results=max_results,
            trace=trace
        ))