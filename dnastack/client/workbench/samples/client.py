from typing import List, Iterator, Optional
from urllib.parse import urljoin

from dnastack.client.models import ServiceEndpoint
from dnastack.client.result_iterator import ResultIterator
from dnastack.client.service_registry.models import ServiceType
from dnastack.client.workbench.base_client import BaseWorkbenchClient, WorkbenchResultLoader
from dnastack.client.workbench.samples.models import SampleListOptions, SampleListResponse, Sample, \
    SampleFilesListOptions, SampleFileListResponse, InstrumentListResponse, InstrumentListOptions
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