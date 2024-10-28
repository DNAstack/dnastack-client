import json
import random
import tempfile
import zipfile
from datetime import datetime
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

from pydantic import BaseModel
from requests import delete

from dnastack import ServiceEndpoint
from dnastack.client.factory import EndpointRepository
from dnastack.client.workbench.ewes.client import EWesClient
from dnastack.client.workbench.ewes.models import MinimalExtendedRun, ExtendedRunRequest, BatchRunResponse, \
    BatchRunRequest, EngineParamPreset
from dnastack.client.workbench.storage.models import StorageAccount, Platform
from dnastack.client.workbench.workflow.client import WorkflowClient
from dnastack.client.workbench.workflow.models import Workflow, WorkflowCreate, WorkflowVersion, WorkflowTransformation
from dnastack.common.environments import env
from dnastack.http.session import HttpSession
from tests.exam_helper import WithTestUserTestCase
from tests.workbench_user_service_helper import WorkbenchUserServiceHelper

HELLO_WORLD_WORKFLOW = """
task hello {
  String name
  command {
    echo 'hello ${name}!'
  }
  output {
    File response = stdout()
  }

  runtime {
    docker: "debian:jessie"
    cpu: 1
    memory: "3.75 GB"
  }
}
workflow test {
  call hello

  output {
    hello.response
  }
}"""


class EngineOAuthConfig(BaseModel):
    clientId: str
    clientSecret: str
    tokenUri: str
    resource: str
    scope: str


class EngineAdapterConfiguration(BaseModel):
    type: str
    url: str
    oauth_config: Optional[EngineOAuthConfig] = None


class ExecutionEngine(BaseModel):
    id: Optional[str] = None
    version: Optional[str] = None
    name: Optional[str] = None
    updated_at: Optional[str] = None
    created_at: Optional[str] = None
    provider: Optional[str] = None
    region: Optional[str] = None
    default: Optional[bool] = False
    description: Optional[str] = None
    health: Optional[str] = None
    engine_adapter_configuration: Optional[EngineAdapterConfiguration] = None


class BaseWorkbenchTestCase(WithTestUserTestCase):
    workbench_base_url = env('E2E_WORKBENCH_BASE_URL', required=False, default='http://localhost:9191')
    ewes_service_base_url = env('E2E_EWES_SERVICE_BASE_URL', required=False, default='http://localhost:9095')
    workflow_service_base_url = env('E2E_WORKFLOW_SERVICE_BASE_URL', required=False, default='http://localhost:9192')
    execution_engine: ExecutionEngine = ExecutionEngine(
        **json.loads(env('E2E_WORKBENCH_EXECUTION_ENGINE_JSON',
                         required=False,
                         default=ExecutionEngine(
                             name='Cromwell on Local',
                             provider='LOCAL',
                             region='local',
                             default=True,
                             engine_adapter_configuration=EngineAdapterConfiguration(
                                 type='WES_ON_CROMWELL',
                                 url='http://localhost:8090',
                                 oauth_config=EngineOAuthConfig(
                                     clientId='ewes-service',
                                     clientSecret='dev-secret-never-use-in-prod',
                                     tokenUri='http://localhost:8081/oauth/token',
                                     resource='http://localhost:8090/',
                                     scope='wes'
                                 )
                             )
                         ).json())))
    namespace: str = None
    hello_world_workflow: Workflow = None
    engine_params = {
        "id": "presetId",
        "name": "presetName",
        "preset_values": {
            "key1": "value1",
            "key2": "value2"
        },
        "default": True,
    }
    health_checks = {
        "checks": [
            {
                "type": "CONNECTIVITY",
                "outcome": "SUCCESS",
            }
        ],
        "namespace": "test-68009138-d945-492e-9c51-af7c80f64366",
        "engine_id": "cromwell-on-google-cloud-platform-lle",
        "outcome": "SUCCESS",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.platform = None
        self.storage_account = None


    @classmethod
    def get_factory(cls) -> EndpointRepository:
        return cls.get_context_manager().use(cls.get_context_urls()[0], no_auth=True)

    @classmethod
    def get_context_urls(cls) -> List[str]:
        return [f'{cls.workbench_base_url}/api/service-registry']

    @classmethod
    def get_app_url(cls) -> str:
        return cls.workbench_base_url

    @classmethod
    def do_on_setup_class_before_auth(cls) -> None:
        super().do_on_setup_class_before_auth()
        cls.namespace = WorkbenchUserServiceHelper().register_user(cls.test_user.email).default_namespace

        with cls._wallet_helper.login_to_app(cls.workbench_base_url,
                                             cls.test_user.email,
                                             cls.test_user.personalAccessToken) as session:
            cls.execution_engine = cls._create_execution_engine(session)
            cls.engine_params = cls._add_execution_engine_parameter(session, cls.execution_engine.id)
            cls._base_logger.info(f'Class {cls.__name__}: Created execution engine: {cls.execution_engine}')

    @classmethod
    def do_on_teardown_class(cls) -> None:
        with cls._wallet_helper.login_to_app(cls.workbench_base_url,
                                             cls.test_user.email,
                                             cls.test_user.personalAccessToken) as session:
            cls._base_logger.info(f'Class {cls.__name__}: Cleaning up namespace: {cls.namespace}')
            cls._cleanup_namespace(session)

        # Delete test user and policy as last
        super().do_on_teardown_class()

    @classmethod
    def _get_ewes_service_endpoints(cls) -> List[ServiceEndpoint]:
        # noinspection PyUnresolvedReferences
        factory: EndpointRepository = cls.get_factory()

        return [
            endpoint
            for endpoint in factory.all()
            if endpoint.type in EWesClient.get_supported_service_types()
        ]

    @classmethod
    def get_ewes_client(cls, index: int = 0) -> Optional[EWesClient]:
        compatible_endpoints = cls._get_ewes_service_endpoints()

        if not compatible_endpoints:
            raise RuntimeError('No ewes-service compatible endpoints for this test')

        if index >= len(compatible_endpoints):
            raise RuntimeError(f'Requested ewes-service compatible endpoint #{index} but it does not exist.')

        compatible_endpoint = compatible_endpoints[index]

        return EWesClient.make(compatible_endpoint, cls.namespace)

    @classmethod
    def _get_workflows_service_endpoints(cls) -> List[ServiceEndpoint]:
        # noinspection PyUnresolvedReferences
        factory: EndpointRepository = cls.get_factory()

        return [
            endpoint
            for endpoint in factory.all()
            if endpoint.type in WorkflowClient.get_supported_service_types()
        ]

    @classmethod
    def get_workflows_client(cls, index: int = 0) -> Optional[WorkflowClient]:
        compatible_endpoints = cls._get_workflows_service_endpoints()

        if not compatible_endpoints:
            raise RuntimeError('No workflow-service compatible endpoints for this test')

        if index >= len(compatible_endpoints):
            raise RuntimeError(f'Requested workflow-service compatible endpoint #{index} but it does not exist.')

        compatible_endpoint = compatible_endpoints[index]

        return WorkflowClient.make(compatible_endpoint, cls.namespace)

    @classmethod
    def _create_execution_engine(cls, session: HttpSession) -> ExecutionEngine:
        response = session.post(urljoin(cls.workbench_base_url, f'/services/ewes-service/{cls.namespace}/engines'),
                                json=cls.execution_engine.dict())
        return ExecutionEngine(**response.json())

    @classmethod
    def _add_execution_engine_parameter(cls, session: HttpSession, engine_id: str) -> EngineParamPreset:
        response = session.post(urljoin(cls.workbench_base_url,
                                        f'/services/ewes-service/{cls.namespace}/engines/{engine_id}/param-presets'),
                                json=cls.engine_params)
        return EngineParamPreset(**response.json())

    @classmethod
    def _cleanup_namespace(cls, session: HttpSession) -> None:
        access_token = cls._wallet_helper.get_access_token(f'{cls.ewes_service_base_url}/', 'namespace')
        session.delete(urljoin(cls.ewes_service_base_url, cls.namespace),
                       headers={'Authorization': f'Bearer {access_token}'})
        access_token = cls._wallet_helper.get_access_token(f'{cls.workflow_service_base_url}/', 'namespace')
        session.delete(urljoin(cls.workflow_service_base_url, cls.namespace),
                       headers={'Authorization': f'Bearer {access_token}'})

    def create_hello_world_workflow(self) -> None:
        workflow_client: WorkflowClient = self.get_workflows_client()
        with open('main.wdl', 'w') as main_wdl_file:
            main_wdl_file.write(HELLO_WORLD_WORKFLOW)
        self.hello_world_workflow = workflow_client.create_workflow(WorkflowCreate(
            entrypoint="main.wdl",
            files=[Path("main.wdl")]
        ))

    def get_hello_world_workflow_url(self) -> str:
        if not self.hello_world_workflow:
            self.create_hello_world_workflow()
        return f"{self.hello_world_workflow.internalId}/{self.hello_world_workflow.latestVersion}"

    def submit_hello_world_workflow_run(self) -> MinimalExtendedRun:
        ewes_client: EWesClient = self.get_ewes_client()
        return ewes_client.submit_run(ExtendedRunRequest(
            workflow_url=self.get_hello_world_workflow_url(),
            workflow_type='WDL',
            workflow_type_version='draft-2',
            workflow_params={
                'test.hello.name': 'foo'
            }
        ))

    def submit_hello_world_workflow_batch(self) -> BatchRunResponse:
        if not self.hello_world_workflow:
            self.create_hello_world_workflow()
        ewes_client: EWesClient = self.get_ewes_client()
        return ewes_client.submit_batch(BatchRunRequest(
            workflow_url=self.get_hello_world_workflow_url(),
            workflow_type='WDL',
            workflow_type_version='draft-2',
            run_requests=[
                ExtendedRunRequest(
                    workflow_params={
                        'test.hello.name': 'foo'
                    }
                ),
                ExtendedRunRequest(
                    workflow_params={
                        'test.hello.name': 'bar'
                    }
                )
            ]
        ))

    @staticmethod
    def _create_workflow_files():
        main_wdl_filename = "main.wdl"
        with open(main_wdl_filename, 'w') as main_wdl_file:
            main_wdl_file.write("""
            version 1.0

            workflow no_task_workflow {
                input {
                    String first_name
                    String? last_name
                }
            }
            """)
        with zipfile.ZipFile('workflow.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(main_wdl_filename)

    @staticmethod
    def _create_description_file():
        with open('description.md', 'w') as description_file:
            description_file.write("""
            TITLE
            DESCRIPTION
            """)

    def _create_workflow(self, use_zip_file: bool = False) -> Workflow:
        return Workflow(**self.simple_invoke(
            'workbench', 'workflows', 'create',
            '--entrypoint', "main.wdl",
            'workflow.zip' if use_zip_file else "main.wdl",
        ))

    def _create_workflow_version(self, workflow_id, name, use_zip_file: bool = False) -> WorkflowVersion:
        return WorkflowVersion(**self.simple_invoke(
            'workbench', 'workflows', 'versions', 'create',
            '--workflow', workflow_id,
            '--name', name,
            '--entrypoint', "main.wdl",
            'workflow.zip' if use_zip_file else "main.wdl",
        ))

    @staticmethod
    def _create_inputs_json_file():
        with tempfile.NamedTemporaryFile(delete=False) as inputs_json_file:
            inputs_json_file.write(b'{"test.hello.name": "bar"}')
            return inputs_json_file.name

    @staticmethod
    def _create_inputs_text_file():
        with tempfile.NamedTemporaryFile(delete=False) as input_text_fp:
            input_text_fp.write(b'bar')
            return input_text_fp.name

    @staticmethod
    def _create_transformation_script_file():
        with tempfile.NamedTemporaryFile(delete=False) as transformation_file:
            transformation_file.write(b"""
                            const myTransformation = (context) => { 
                                return { 'baz': 'waz' } 
                            }
                            """)
            return transformation_file.name

    def _create_workflow_transformation(self, workflow_id, version_id,
                                        script_from_file: bool = False) -> WorkflowTransformation:

        if script_from_file:
            transformation_script = self._create_transformation_script_file()

        return WorkflowTransformation(**self.simple_invoke(
            'workbench', 'workflows','versions', 'transformations', 'create',
            '--workflow', workflow_id,
            '--version', version_id,
            '--label', "test",
            '--label', "can-be-deleted",
            f'@{transformation_script}' if script_from_file else "(context) => { return { 'foo': 'bar' } }"
        ))

    def _create_storage_account(self, id=None) -> StorageAccount:
        if not id:
            id = f'test-storage-account-{random.randint(0, 100000)}'
        return StorageAccount(**self.simple_invoke(
            'workbench', 'storage', 'add', 'aws',
            id,
            '--name', 'Test Storage Account',
            '--access-key-id', env('E2E_AWS_ACCESS_KEY_ID', required=True),
            '--secret-access-key', env('E2E_AWS_SECRET_ACCESS_KEY', required=True),
            '--region', env('E2E_AWS_REGION', default='ca-central-1'),
            '--bucket', env('E2E_AWS_BUCKET', default='s3://dnastack-workbench-sample-service-e2e-test')
        ))

    def _get_or_create_storage_account(self) -> StorageAccount:
        if not self.storage_account:
            self.storage_account = self._create_storage_account()
        return self.storage_account

    def _create_platform(self, created_storage_account: StorageAccount, id=None) -> Platform:
        if not id:
            id = f'test-storage-account-{random.randint(0, 100000)}'

        path = env('E2E_AWS_BUCKET', required=False, default='/dnastack-workbench-sample-service-e2e-test')

        # Replace s3:// with /
        if path.startswith('s3://'):
            path = path.replace('s3://', '/')

        return Platform(**self.simple_invoke(
            'workbench', 'storage', 'platforms', 'add',
            id,
            '--name', 'Test Platform',
            '--storage-id', created_storage_account.id,
            '--platform', 'PACBIO',
            '--path', path
        ))

    def _get_or_create_platform(self) -> Platform:
        if not self.platform:
            self.platform = self._create_platform(self._get_or_create_storage_account())

        return self.platform
