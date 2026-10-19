from contextlib import contextmanager
from http.client import HTTPConnection
from typing import Any, Dict, List, Iterator, Optional, Type, TypeVar, Union, Iterable
from urllib.parse import quote, urljoin

from pydantic import BaseModel, ValidationError

from dnastack.client.models import ServiceEndpoint
from dnastack.client.result_iterator import ResultIterator
from dnastack.client.service_registry.models import ServiceType
from dnastack.client.workbench.base_client import BaseWorkbenchClient, WorkbenchResultLoader
from dnastack.client.workbench.ewes.engine_models import EngineParamPresetRequest, ExecutionEngineRequest
from dnastack.client.workbench.ewes.models import ExtendedRunEvents, WesServiceInfo, ExtendedRunStatus, \
    ExtendedRunListOptions, \
    ExtendedRunListResponse, ExtendedRun, RunId, WorkbenchApiError, BatchActionResult, MinimalExtendedRun, \
    BatchRunResponse, BatchRunRequest, ExtendedRunRequest, Log, TaskListOptions, \
    TaskListResponse, LogType, ExecutionEngineListOptions, ExecutionEngineListResponse, ExecutionEngine, \
    EngineParamPreset, EngineParamPresetListOptions, EngineParamPresetListResponse, \
    EngineHealthCheck, EngineHealthCheckListOptions, EngineHealthCheckListResponse, \
    Hook, HookListResponse, SimpleSample, UpdateRunSamplesRequest
from dnastack.common.tracing import Span
from dnastack.http.session import HttpSession, JsonPatch


def _path_segment(value: str) -> str:
    """Escape a user-supplied id so that it names one path segment, or reject it if no encoding can."""
    # requests un-escapes %2E when it re-quotes a URL, and urllib3 then removes '.' and '..' segments.
    # No encoding keeps those ids inside one segment, and an empty id would address the collection.
    if value in ('', '.', '..'):
        raise ValueError(f"'{value}' is not a valid id")
    return quote(value, safe='')


_ResponseModel = TypeVar('_ResponseModel', bound=BaseModel)


class UnreadableEngineResponseError(Exception):
    """The engines service returned an engine or preset that does not match the model this client reads."""


def _read_engine_response(model: Type[_ResponseModel], body: Dict[str, Any], what: str) -> _ResponseModel:
    """Parse a response to an engine or preset write, without echoing any of its values on failure.

    A pydantic error message quotes the offending input, and the body of an engine response may hold a
    credential, so the message is rebuilt from each error's location and reason only.
    """
    try:
        return model(**body)
    except ValidationError as e:
        problems = '; '.join(
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}" for error in e.errors()
        )
    # Raised outside the except block so that the ValidationError, which quotes the input, is not chained.
    raise UnreadableEngineResponseError(f'The engines service returned {what} this CLI cannot read: {problems}')


class ExtendedRunListResultLoader(WorkbenchResultLoader):

    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Span,
                 list_options: Optional[ExtendedRunListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> ExtendedRunListOptions:
        return ExtendedRunListOptions()

    def extract_api_response(self, response_body: dict) -> ExtendedRunListResponse:
        return ExtendedRunListResponse(**response_body)


class TaskListResultLoader(WorkbenchResultLoader):

    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Span,
                 list_options: Optional[TaskListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> TaskListOptions:
        return TaskListOptions()

    def extract_api_response(self, response_body: dict) -> TaskListResponse:
        return TaskListResponse(**response_body)


class EngineListResultLoader(WorkbenchResultLoader):
    def __init(self,
               service_url: str,
               http_session: HttpSession,
               trace: Span,
               list_options: Optional[ExecutionEngineListOptions] = None,
               max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> ExecutionEngineListOptions:
        return ExecutionEngineListOptions()

    def extract_api_response(self, response_body: dict) -> ExecutionEngineListResponse:
        return ExecutionEngineListResponse(**response_body)


class EngineParamPresetListResultLoader(WorkbenchResultLoader):
    def __init(self,
               service_url: str,
               http_session: HttpSession,
               trace: Span,
               list_options: Optional[ExecutionEngineListOptions] = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         trace=trace)

    def get_new_list_options(self) -> EngineParamPresetListOptions:
        return EngineParamPresetListOptions()

    def extract_api_response(self, response_body: dict) -> EngineParamPresetListResponse:
        return EngineParamPresetListResponse(**response_body)


class EngineHealthCheckListResultLoader(WorkbenchResultLoader):
    def __init(self,
               service_url: str,
               http_session: HttpSession,
               trace: Span,
               list_options: Optional[ExecutionEngineListOptions] = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         trace=trace)

    def get_new_list_options(self) -> EngineHealthCheckListOptions:
        return EngineHealthCheckListOptions()

    def extract_api_response(self, response_body: dict) -> EngineHealthCheckListResponse:
        return EngineHealthCheckListResponse(**response_body)


@contextmanager
def _without_wire_debugging():
    # Engine create/update bodies carry credentials, and http.client's wire debugging (debug mode) prints
    # request bodies verbatim.
    saved = HTTPConnection.debuglevel
    HTTPConnection.debuglevel = 0
    try:
        yield
    finally:
        HTTPConnection.debuglevel = saved


class EWesClient(BaseWorkbenchClient):

    @staticmethod
    def get_adapter_type() -> str:
        return 'ewes-service'

    @staticmethod
    def get_supported_service_types() -> List[ServiceType]:
        return [
            ServiceType(group='com.dnastack.workbench', artifact='ewes-service', version='1.0.0'),
        ]

    # noinspection PyMethodOverriding
    @classmethod
    def make(cls, endpoint: ServiceEndpoint, namespace: str):
        """Create this class with the given `endpoint` and `namespace`."""
        if not endpoint.type:
            endpoint.type = cls.get_default_service_type()
        return cls(endpoint, namespace)

    def get_service_info(self, trace: Optional[Span] = None) -> WesServiceInfo:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/service-info'),
                                   trace_context=trace)
            return WesServiceInfo(**response.json())

    def list_runs(self,
                  list_options: Optional[ExtendedRunListOptions] = None,
                  max_results: int = None,
                  trace: Optional[Span] = None) -> Iterator[ExtendedRunStatus]:
        trace = trace or Span(origin=self)
        return ResultIterator(ExtendedRunListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs'),
            http_session=self.create_http_session(),
            list_options=list_options,
            max_results=max_results,
            trace=trace,
        ))

    def get_status(self, run_id: str, trace: Optional[Span] = None) -> MinimalExtendedRun:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}/status'),
                                   trace_context=trace)
            return MinimalExtendedRun(**response.json())

    def get_run(self, run_id: str, include_tasks: bool = False, trace: Optional[Span] = None) -> ExtendedRun:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}'
                                                              f'?exclude_tasks={not include_tasks}'),
                                   trace_context=trace)
            return ExtendedRun(**response.json())

    def cancel_run(self, run_id: str, trace: Optional[Span] = None) -> Union[RunId, WorkbenchApiError]:
        with self.create_http_session() as session:
            response = session.post(urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}/cancel'),
                                    trace_context=trace)
            return RunId(**response.json())

    def cancel_runs(self, run_ids: List[str], trace: Optional[Span] = None) -> BatchActionResult:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.post(urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/cancel'),
                                    json=run_ids,
                                    trace_context=trace)
            return BatchActionResult(**response.json())

    def delete_runs(self, run_ids: List[str], trace: Optional[Span] = None) -> BatchActionResult:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.post(urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/delete'),
                                    json=run_ids,
                                    trace_context=trace)
            return BatchActionResult(**response.json())

    def submit_run(self, data: ExtendedRunRequest, trace: Optional[Span] = None) -> MinimalExtendedRun:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.post(urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs'),
                                    json=data.model_dump(),
                                    trace_context=trace)
        return MinimalExtendedRun(**response.json())

    def submit_batch(self, data: BatchRunRequest, trace: Optional[Span] = None) -> BatchRunResponse:
        with self.create_http_session() as session:
            response = session.post(urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/batch'),
                                    json=data.model_dump(),
                                    trace_context=trace)
        return BatchRunResponse(**response.json())

    def stream_run_logs(self,
                        run_id: str,
                        log_type: LogType = LogType.STDOUT,
                        max_bytes: Optional[int] = None,
                        offset: Optional[int] = None,
                        trace: Optional[Span] = None) -> Iterable[bytes]:
        return self.stream_log_url(
            urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}/logs/{log_type}'),
            max_bytes,
            offset,
            trace=trace,
        )

    def stream_task_logs(self,
                         run_id: str,
                         task_id: str,
                         log_type: LogType = LogType.STDOUT,
                         max_bytes: Optional[int] = None,
                         offset: Optional[int] = None,
                         trace: Optional[Span] = None) -> Iterable[bytes]:
        return self.stream_log_url(
            urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}/tasks/{task_id}/logs/{log_type}'),
            max_bytes,
            offset,
            trace=trace,
        )

    def stream_log_url(self,
                       log_url: str,
                       max_bytes: Optional[int],
                       offset: Optional[int],
                       trace: Optional[Span] = None) -> Iterable[bytes]:
        trace = trace or Span()

        params = {}
        if max_bytes:
            params['max'] = max_bytes

        if offset:
            params['offset'] = offset

        with self.create_http_session() as session:
            with session.get(urljoin(self.endpoint.url, log_url),
                             params=params,
                             stream=True,
                             trace_context=trace) as response:
                if 'Content-Length' in response.headers and int(response.headers['Content-Length']) == 0:
                    yield None
                    return
                for chunk in response.iter_content(chunk_size=None):
                    yield chunk

    def list_tasks(self,
                   run_id: str,
                   list_options: Optional[TaskListOptions] = None,
                   max_results: int = None,
                   trace: Optional[Span] = None) -> Iterator[Log]:
        trace = trace or Span(origin=self)
        return ResultIterator(TaskListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}/tasks'),
            http_session=self.create_http_session(),
            list_options=list_options,
            max_results=max_results,
            trace=trace,
        ))
    
    def list_events(self, run_id: str, include_tasks: bool = False, trace: Optional[Span] = None) -> ExtendedRunEvents:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}'
                                                              f'?exclude_tasks={not include_tasks}'),
                                   trace_context=trace)
            return ExtendedRunEvents(**response.json())


    def list_hooks(self, run_id: str, trace: Optional[Span] = None) -> HookListResponse:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}/hooks'),
                trace_context=trace,
            )
            return HookListResponse(**response.json())

    def get_hook(self, run_id: str, hook_id: str, trace: Optional[Span] = None) -> Hook:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}/hooks/{hook_id}'),
                trace_context=trace,
            )
            return Hook(**response.json())

    def update_run_samples(self, run_id: str, samples: List[SimpleSample], trace: Optional[Span] = None) -> ExtendedRunStatus:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            request = UpdateRunSamplesRequest(samples=samples)
            response = session.submit(
                method='put',
                url=urljoin(self.endpoint.url, f'{self.namespace}/ga4gh/wes/v1/runs/{run_id}/samples'),
                json=request.model_dump(by_alias=True),
                trace_context=trace
            )
            return ExtendedRunStatus(**response.json())

    def _engine_url(self, engine_id: str, suffix: str = '') -> str:
        return urljoin(self.endpoint.url, f'{self.namespace}/engines/{_path_segment(engine_id)}{suffix}')

    def _engine_param_preset_url(self, engine_id: str, param_preset_id: str) -> str:
        return self._engine_url(engine_id, f'/param-presets/{_path_segment(param_preset_id)}')

    def list_engines(self,
                     list_options: ExecutionEngineListOptions,
                     max_results: int = None,
                     trace: Optional[Span] = None) -> Iterable[ExecutionEngine]:
        trace = trace or Span(origin=self)
        return ResultIterator(EngineListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/engines'),
            http_session=self.create_http_session(log_response_body=False),
            list_options=list_options,
            max_results=max_results,
            trace=trace,
        ))

    def get_engine(self,
                   engine_id: str,
                   trace: Optional[Span] = None) -> ExecutionEngine:
        with self.create_http_session(log_response_body=False) as session:
            response = session.get(self._engine_url(engine_id), trace_context=trace)
            return ExecutionEngine(**response.json())

    def list_engine_param_presets(self,
                                  engine_id: str,
                                  list_options: EngineParamPresetListOptions,
                                  trace: Optional[Span] = None) -> Iterable[EngineParamPreset]:
        trace = trace or Span(origin=self)
        return ResultIterator(EngineParamPresetListResultLoader(
            service_url=self._engine_url(engine_id, '/param-presets'),
            http_session=self.create_http_session(),
            list_options=list_options,
            trace=trace,
        ))

    def get_engine_param_preset(self,
                                engine_id: str,
                                param_preset_id: str,
                                trace: Optional[Span] = None) -> EngineParamPreset:
        with self.create_http_session() as session:
            response = session.get(self._engine_param_preset_url(engine_id, param_preset_id), trace_context=trace)
            return EngineParamPreset(**response.json())

    def create_engine(self, engine: ExecutionEngineRequest, trace: Optional[Span] = None) -> ExecutionEngine:
        trace = trace or Span(origin=self)
        with self.create_http_session(log_response_body=False) as session:
            with _without_wire_debugging():
                response = session.post(urljoin(self.endpoint.url, f'{self.namespace}/engines'),
                                        json=engine.to_request_body(),
                                        trace_context=trace)
            return _read_engine_response(ExecutionEngine, response.json(), 'an engine')

    def update_engine(self,
                      engine_id: str,
                      engine: ExecutionEngineRequest,
                      if_match: str,
                      trace: Optional[Span] = None) -> ExecutionEngine:
        trace = trace or Span(origin=self)
        with self.create_http_session(log_response_body=False) as session:
            with _without_wire_debugging():
                response = session.put(self._engine_url(engine_id),
                                       json=engine.to_request_body(),
                                       headers={'If-Match': if_match},
                                       trace_context=trace)
            return _read_engine_response(ExecutionEngine, response.json(), 'an engine')

    def patch_engine(self,
                     engine_id: str,
                     patches: List[JsonPatch],
                     if_match: str,
                     trace: Optional[Span] = None) -> ExecutionEngine:
        trace = trace or Span(origin=self)
        with self.create_http_session(log_response_body=False) as session:
            response = session.json_patch(self._engine_url(engine_id),
                                          json=[p.model_dump(exclude_none=True) for p in patches],
                                          headers={'If-Match': if_match},
                                          trace_context=trace)
            return _read_engine_response(ExecutionEngine, response.json(), 'an engine')

    def delete_engine(self, engine_id: str, trace: Optional[Span] = None) -> None:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            session.delete(self._engine_url(engine_id), trace_context=trace)

    def create_engine_param_preset(self,
                                   engine_id: str,
                                   preset: EngineParamPresetRequest,
                                   trace: Optional[Span] = None) -> EngineParamPreset:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.post(self._engine_url(engine_id, '/param-presets'),
                                    json=preset.to_request_body(),
                                    trace_context=trace)
            return _read_engine_response(EngineParamPreset, response.json(), 'a parameter preset')

    def update_engine_param_preset(self,
                                   engine_id: str,
                                   param_preset_id: str,
                                   preset: EngineParamPresetRequest,
                                   if_match: str,
                                   trace: Optional[Span] = None) -> EngineParamPreset:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.put(
                self._engine_param_preset_url(engine_id, param_preset_id),
                json=preset.to_request_body(),
                headers={'If-Match': if_match},
                trace_context=trace)
            return _read_engine_response(EngineParamPreset, response.json(), 'a parameter preset')

    def patch_engine_param_preset(self,
                                  engine_id: str,
                                  param_preset_id: str,
                                  patches: List[JsonPatch],
                                  if_match: str,
                                  trace: Optional[Span] = None) -> EngineParamPreset:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.json_patch(
                self._engine_param_preset_url(engine_id, param_preset_id),
                json=[p.model_dump(exclude_none=True) for p in patches],
                headers={'If-Match': if_match},
                trace_context=trace)
            return _read_engine_response(EngineParamPreset, response.json(), 'a parameter preset')

    def delete_engine_param_preset(self, engine_id: str, param_preset_id: str, trace: Optional[Span] = None) -> None:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            session.delete(
                self._engine_param_preset_url(engine_id, param_preset_id),
                trace_context=trace)

    def list_engine_health_checks(self,
                                  engine_id: str,
                                  list_options: EngineHealthCheckListOptions,
                                  max_results: int = None,
                                  trace: Optional[Span] = None) -> Iterable[EngineHealthCheck]:
        trace = trace or Span(origin=self)
        return ResultIterator(EngineHealthCheckListResultLoader(
            service_url=self._engine_url(engine_id, '/health-checks'),
            http_session=self.create_http_session(),
            list_options=list_options,
            max_results=max_results,
            trace=trace,
        ))
