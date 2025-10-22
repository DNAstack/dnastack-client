from typing import List, Iterator, Optional
from urllib.parse import urljoin

from dnastack.client.models import ServiceEndpoint
from dnastack.client.result_iterator import ResultIterator
from dnastack.client.service_registry.models import ServiceType
from dnastack.client.workbench.base_client import BaseWorkbenchClient
from dnastack.client.workbench.base_client import WorkbenchResultLoader
from dnastack.client.workbench.workflow.models import WorkflowDescriptor, WorkflowListResponse, Workflow, \
    WorkflowCreate, \
    WorkflowVersionCreate, WorkflowVersion, WorkflowVersionListResponse, WorkflowListOptions, \
    WorkflowVersionListOptions, WorkflowFile, WorkflowDefaultsListResponse, WorkflowDefaultsListOptions, \
    WorkflowTransformationListOptions, WorkflowTransformationListResponse, WorkflowDefaults, WorkflowDefaultsSelector, \
    ResolvedWorkflow, WorkflowDefaultsUpdateRequest, WorkflowTransformation, WorkflowTransformationCreate, \
    WorkflowDefaultsCreateRequest, WorkflowDependency, WorkflowDependencyListResponse, WorkflowDependencyListOptions, \
    WorkflowDependencyCreateRequest, WorkflowDependencyUpdateRequest
from dnastack.common.tracing import Span
from dnastack.http.session import JsonPatch, HttpSession


class WorkflowDefaultsListResultLoader(WorkbenchResultLoader):
    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Optional[Span],
                 list_options: Optional[WorkflowDefaultsListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> WorkflowDefaultsListOptions:
        return WorkflowDefaultsListOptions()

    def extract_api_response(self, response_body: dict) -> WorkflowDefaultsListResponse:
        return WorkflowDefaultsListResponse(**response_body)

class WorkflowsListResultLoader(WorkbenchResultLoader):
    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Optional[Span],
                 list_options: Optional[WorkflowListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> WorkflowListOptions:
        return WorkflowListOptions()

    def extract_api_response(self, response_body: dict) -> WorkflowListResponse:
        return WorkflowListResponse(**response_body)

class WorkflowTransformationsListResultLoader(WorkbenchResultLoader):
    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Optional[Span],
                 list_options: Optional[WorkflowTransformationListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> WorkflowTransformationListOptions:
        return WorkflowTransformationListOptions()

    def extract_api_response(self, response_body: dict) -> WorkflowTransformationListResponse:
        return WorkflowTransformationListResponse(**response_body)

class WorkflowVersionsListResultLoader(WorkbenchResultLoader):
    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Optional[Span],
                 list_options: Optional[WorkflowVersionListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> WorkflowVersionListOptions:
        return WorkflowVersionListOptions()

    def extract_api_response(self, response_body: dict) -> WorkflowVersionListResponse:
        return WorkflowVersionListResponse(**response_body)


class WorkflowDependencyListResultLoader(WorkbenchResultLoader):
    def __init__(self,
                 service_url: str,
                 http_session: HttpSession,
                 trace: Optional[Span],
                 list_options: Optional[WorkflowDependencyListOptions] = None,
                 max_results: int = None):
        super().__init__(service_url=service_url,
                         http_session=http_session,
                         list_options=list_options,
                         max_results=max_results,
                         trace=trace)

    def get_new_list_options(self) -> WorkflowDependencyListOptions:
        return WorkflowDependencyListOptions()

    def extract_api_response(self, response_body: dict) -> WorkflowDependencyListResponse:
        return WorkflowDependencyListResponse(**response_body)


class WorkflowClient(BaseWorkbenchClient):

    @staticmethod
    def get_adapter_type() -> str:
        return 'workflow-service'

    @staticmethod
    def get_supported_service_types() -> List[ServiceType]:
        return [
            ServiceType(group='com.dnastack.workbench', artifact='workflow-service', version='1.0.0'),
        ]

    # noinspection PyMethodOverriding
    @classmethod
    def make(cls, endpoint: ServiceEndpoint, namespace: str):
        """Create this class with the given `endpoint` and `namespace`."""
        if not endpoint.type:
            endpoint.type = cls.get_default_service_type()
        return cls(endpoint, namespace)

    def get_json_schema(self, workflow_id: str, version_id: str) -> WorkflowDescriptor:
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}/describe'))
        return WorkflowDescriptor(**response.json())

    def list_workflows(self,
                       list_options: Optional[WorkflowListOptions] = None,
                       max_results: int = None) -> Iterator[Workflow]:
        return ResultIterator(WorkflowsListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/workflows'),
            http_session=self.create_http_session(),
            list_options=list_options,
            max_results=max_results,
            trace=None
        ))

    def list_workflow_versions(self,
                               workflow_id: str,
                               list_options: Optional[WorkflowVersionListOptions] = None,
                               max_results: int = None) -> Iterator[WorkflowVersion]:
        return ResultIterator(WorkflowVersionsListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions'),
            http_session=self.create_http_session(),
            list_options=list_options,
            trace=None,
            max_results=max_results))

    def get_workflow(self, workflow_id: str, include_deleted: Optional[bool] = False) -> Workflow:
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}?deleted={include_deleted}'))
            workflow = Workflow(**response.json())
            workflow.etag = response.headers.get("Etag").strip("\"")
            return workflow

    def get_workflow_version(self, workflow_id: str, version_id: str,
                             include_deleted: Optional[bool] = False) -> WorkflowVersion:
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url,
                        f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}?deleted={include_deleted}'))
            workflow_version = WorkflowVersion(**response.json())
            workflow_version.etag = response.headers.get("Etag").strip("\"")
            return workflow_version

    def get_workflow_files(self, workflow_id: str, version_id: str) -> List[WorkflowFile]:
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url,
                        f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}/files'))
            return [
                WorkflowFile(**item)
                for item in response.json()
            ]

    # not used yet, being saved for when the API changes
    def get_workflow_descriptor(self, workflow_id: str, version_id: str) -> WorkflowFile:
        with self.create_http_session() as session:
            with session.get(
                    urljoin(self.endpoint.url,
                            f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}/descriptor')
            )as response:
                if int(response.headers['Content-Length']) == 0:
                    yield None
                    return
                for chunk in response.iter_content(chunk_size=None):
                    yield chunk

    @staticmethod
    def _prepare_workflow_files(files):
        workflow_files = []
        for file in files:
            with open(file, 'rb') as f:
                workflow_files.append(('workflow_file', (file.name, f.read())))
        return workflow_files

    def create_workflow(self, workflow_create_request: WorkflowCreate) -> Workflow:
        with self.create_http_session() as session:
            data = {
                'name': (None, workflow_create_request.name),
                'version_name': (None, workflow_create_request.version_name),
                'organization': (None, workflow_create_request.organization),
                'description': (None, workflow_create_request.description),
                'entrypoint': (None, workflow_create_request.entrypoint),
                'labels': (None, workflow_create_request.labels)
            }
            response = session.post(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows'),
                data=data,
                files=self._prepare_workflow_files(workflow_create_request.files)
            )
        return Workflow(**response.json())

    def create_version(self, workflow_id: str,
                       workflow_version_create_request: WorkflowVersionCreate) -> WorkflowVersion:
        with self.create_http_session() as session:
            data = {
                'version_name': (None, workflow_version_create_request.version_name),
                'entrypoint': (None, workflow_version_create_request.entrypoint),
            }
            response = session.post(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions'),
                data=data,
                files=self._prepare_workflow_files(workflow_version_create_request.files)
            )
        return WorkflowVersion(**response.json())

    def delete_workflow(self, workflow_id: str, etag: str):
        with self.create_http_session() as session:
            session.delete(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}'),
                headers={'If-Match': etag}
            )

    def delete_workflow_version(self, workflow_id: str, version_id: str, etag: str):
        with self.create_http_session() as session:
            session.delete(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}'),
                headers={'If-Match': etag}
            )

    def update_workflow(self, workflow_id: str, etag: str, updates: List[JsonPatch]) -> Workflow:
        with self.create_http_session() as session:
            updates = [update.model_dump() for update in updates]
            response = session.json_patch(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}'),
                headers={'If-Match': etag},
                json=updates
            )
            return Workflow(**response.json())

    def update_workflow_version(self, workflow_id: str, version_id: str, etag: str,
                                updates: List[JsonPatch]) -> WorkflowVersion:
        with self.create_http_session() as session:
            updates = [update.model_dump() for update in updates]
            response = session.json_patch(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}'),
                headers={'If-Match': etag},
                json=updates
            )
            return WorkflowVersion(**response.json())

    def resolve_workflow(self, workflow_url: str) -> ResolvedWorkflow:
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/resolve'),
                params={"workflow-url": workflow_url}
            )
            return ResolvedWorkflow(**response.json())

    def resolve_workflow_defaults(self, workflow_id: str, workflow_version_id: str,
                                  selector: WorkflowDefaultsSelector) -> WorkflowDefaults:
        with self.create_http_session() as session:
            response = session.post(
                urljoin(self.endpoint.url,
                        f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/defaults/resolve'),
                params={
                    "engine": selector.engine,
                    "provider": selector.provider,
                    "region": selector.region
                }
            )
            return WorkflowDefaults(**response.json())

    def list_workflow_defaults(self, workflow_id: str, version_id: str, max_results: int,
                               list_options: WorkflowDefaultsListOptions) -> Iterator[
        WorkflowDefaults]:
        return ResultIterator(WorkflowDefaultsListResultLoader(
            service_url=urljoin(self.endpoint.url,
                                f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}/defaults'),
            http_session=self.create_http_session(),
            list_options=list_options,
            trace=None,
            max_results=max_results))

    def get_workflow_defaults(self, workflow_id: str, version_id: str, default_id: str) -> WorkflowDefaults:
        with self.create_http_session() as session:
            response = session.get(
                urljoin(self.endpoint.url,
                        f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}/defaults/{default_id}')
            )
            return WorkflowDefaults(**response.json())

    def create_workflow_defaults(self, workflow_id: str, version_id: str,
                                 workflow_defaults: WorkflowDefaultsCreateRequest) -> WorkflowDefaults:
        with self.create_http_session() as session:
            response = session.post(
                urljoin(self.endpoint.url,
                        f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}/defaults'),
                json=workflow_defaults.model_dump()
            )
            return WorkflowDefaults(**response.json())

    def delete_workflow_defaults(self, workflow_id: str, version_id: str, default_id: str, if_match: str):
        with self.create_http_session() as session:
            session.delete(
                urljoin(self.endpoint.url,
                        f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}/defaults/{default_id}'),
                headers={"If-Match": if_match}
            )

    def update_workflow_defaults(self, workflow_id: str, version_id: str, default_id: str, if_match: str,
                                 workflow_defaults: WorkflowDefaultsUpdateRequest):
        with self.create_http_session() as session:
            response = session.submit("PUT",
                urljoin(self.endpoint.url,
                        f'{self.namespace}/workflows/{workflow_id}/versions/{version_id}/defaults/{default_id}'),
                json=workflow_defaults.model_dump(),
                headers={"If-Match": if_match}
            )
            return WorkflowDefaults(**response.json())

    def list_workflow_transformations(self, workflow_id: str, workflow_version_id: str,
                                      list_options: Optional[WorkflowTransformationListOptions] = None,
                                      max_results: int = None) -> Iterator[WorkflowTransformation]:
        return ResultIterator(WorkflowTransformationsListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/transformations'),
            http_session=self.create_http_session(),
            list_options=list_options,
            max_results=max_results,
            trace=None
        ))

    def get_workflow_transformation(self, workflow_id: str, workflow_version_id: str, transformation_id: str,
                                    trace: Optional[Span] = None) -> WorkflowTransformation:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/transformations/{transformation_id}'),
                                   trace_context=trace)
            return WorkflowTransformation(**response.json())

    def delete_workflow_transformation(self, workflow_id: str, workflow_version_id: str, transformation_id: str):
        with self.create_http_session() as session:
            session.delete(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/transformations/{transformation_id}'),
            )

    def create_workflow_transformation(self, workflow_id: str, workflow_version_id: str,
                                       workflow_transformation_create_request: WorkflowTransformationCreate) -> WorkflowTransformation:
        with self.create_http_session() as session:
            response = session.post(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/transformations'),
                json=workflow_transformation_create_request.model_dump()
            )
        return WorkflowTransformation(**response.json())

    def list_workflow_dependencies(self, workflow_id: str, workflow_version_id: str,
                                   list_options: Optional[WorkflowDependencyListOptions] = None,
                                   max_results: int = None) -> Iterator[WorkflowDependency]:
        return ResultIterator(WorkflowDependencyListResultLoader(
            service_url=urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/dependencies'),
            http_session=self.create_http_session(),
            list_options=list_options,
            max_results=max_results,
            trace=None
        ))

    def get_workflow_dependency(self, workflow_id: str, workflow_version_id: str, dependency_id: str,
                                trace: Optional[Span] = None) -> WorkflowDependency:
        trace = trace or Span(origin=self)
        with self.create_http_session() as session:
            response = session.get(urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/dependencies/{dependency_id}'),
                                   trace_context=trace)
            return WorkflowDependency(**response.json())

    def create_workflow_dependency(self, workflow_id: str, workflow_version_id: str,
                                   workflow_dependency_create_request: WorkflowDependencyCreateRequest,
                                   admin_only_action: bool = False) -> WorkflowDependency:
        headers = {}
        if admin_only_action:
            headers['X-Admin-Only-Action'] = 'true'
        
        with self.create_http_session() as session:
            response = session.post(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/dependencies'),
                json=workflow_dependency_create_request.model_dump(),
                headers=headers
            )
        return WorkflowDependency(**response.json())

    def update_workflow_dependency(self, workflow_id: str, workflow_version_id: str, dependency_id: str,
                                   workflow_dependency_update_request: WorkflowDependencyUpdateRequest,
                                   admin_only_action: bool = False) -> WorkflowDependency:
        headers = {}
        if admin_only_action:
            headers['X-Admin-Only-Action'] = 'true'
        
        with self.create_http_session() as session:
            response = session.submit("PUT",
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/dependencies/{dependency_id}'),
                json=workflow_dependency_update_request.model_dump(),
                headers=headers
            )
        return WorkflowDependency(**response.json())

    def delete_workflow_dependency(self, workflow_id: str, workflow_version_id: str, dependency_id: str,
                                   admin_only_action: bool = False):
        headers = {}
        if admin_only_action:
            headers['X-Admin-Only-Action'] = 'true'
        
        with self.create_http_session() as session:
            session.delete(
                urljoin(self.endpoint.url, f'{self.namespace}/workflows/{workflow_id}/versions/{workflow_version_id}/dependencies/{dependency_id}'),
                headers=headers
            )
