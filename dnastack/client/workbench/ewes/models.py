from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Literal, Union

from pydantic import BaseModel, Field

from dnastack.client.service_registry.models import Service
from dnastack.client.workbench.common.models import State, CaseInsensitiveEnum
from dnastack.client.workbench.models import BaseListOptions, PaginatedResource
from dnastack.common.json_argument_parser import JSONType


class Outcome(str, CaseInsensitiveEnum):
    SUCCESS = 'SUCCESS',
    FAILURE = 'FAILURE'


class LogType(str, CaseInsensitiveEnum):
    STDOUT = 'stdout',
    STDERR = 'stderr',


class WesServiceInfo(Service):
    workflow_type_versions: Optional[Dict] = None
    supported_wes_versions: Optional[List[str]] = None
    supported_filesystem_protocols: Optional[List[str]] = None
    workflow_engine_versions: Optional[Dict] = None
    default_workflow_engine_parameters: Optional[List[Dict]] = None
    system_state_counts: Optional[Dict] = None
    auth_instructions_url: Optional[str] = None
    tags: Optional[Dict] = None

class SimpleSample(BaseModel):
    id: str
    storage_account_id: Optional[str] = None


class ExtendedRunStatus(BaseModel):
    run_id: str
    external_id: Optional[str] = None
    state: State
    start_time: datetime
    end_time: Optional[datetime] = None
    submitted_by: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_version_id: Optional[str] = None
    workflow_url: Optional[str] = None
    workflow_name: Optional[str] = None
    workflow_version: Optional[str] = None
    workflow_authors: Optional[List[str]] = None
    workflow_type: Optional[str] = None
    workflow_type_version: Optional[str] = None
    workflow_params: Optional[Dict] = None
    tags: Optional[Dict] = None
    workflow_engine_parameters: Optional[Dict] = None
    samples: Optional[List[SimpleSample]] = None


class Log(BaseModel):
    task_id: Optional[str] = None
    name: str
    pretty_name: Optional[str] = None
    cmd: Optional[Any] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    state: Optional[State] = None

class RunDependency(BaseModel):
    run_id: str

class ExtendedRunRequest(BaseModel):
    workflow_url: Optional[str] = None
    workflow_name: Optional[str] = None
    workflow_version: Optional[str] = None
    workflow_authors: Optional[List[str]] = None
    workflow_type: Optional[str] = None
    workflow_type_version: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_version_id: Optional[str] = None
    submitted_by: Optional[str] = None
    workflow_params: Optional[Dict] = None
    workflow_engine_parameters: Optional[Dict] = None
    dependencies: Optional[List[RunDependency]] = None
    tags: Optional[Dict] = None
    samples: Optional[List[SimpleSample]] = None


class EventType(str, Enum):
    PREPROCESSING = "PREPROCESSING"
    RUN_SUBMITTED = "RUN_SUBMITTED"
    RUN_SUBMITTED_TO_ENGINE = "RUN_SUBMITTED_TO_ENGINE"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    ENGINE_STATUS_UPDATE = "ENGINE_STATUS_UPDATE"
    STATE_TRANSITION = "STATE_TRANSITION"
    EVENT_METADATA = "EventMetadata"

class SampleId(BaseModel):
    id: Optional[str] = None
    storage_account_id: Optional[str] = None

class RunEventMetadata(BaseModel):
    event_type: Literal[EventType.EVENT_METADATA]
    message: Optional[str] = None


class RunSubmittedMetadata(RunEventMetadata):
    event_type: Literal[EventType.RUN_SUBMITTED]
    start_time: Optional[str] = None
    submitted_by: Optional[str] = None
    state: Optional[State] = None
    workflow_id: Optional[str] = None
    workflow_version_id: Optional[str] = None
    workflow_url: Optional[str] = None
    workflow_name: Optional[str] = None
    workflow_version: Optional[str] = None
    workflow_authors: Optional[List[str]] = None
    workflow_type: Optional[str] = None
    workflow_type_version: Optional[str] = None
    tags: Optional[dict[str, str]] = None
    sample_ids: Optional[List[SampleId]] = None

class PreprocessingMetadata(RunEventMetadata):
    event_type: Literal[EventType.PREPROCESSING]
    outcome: Optional[str] = None

class ErrorOccurredMetadata(RunEventMetadata):
    event_type: Literal[EventType.ERROR_OCCURRED]
    errors: Optional[List[str]] = None

class StateTransitionMetadata(RunEventMetadata):
    event_type: Literal[EventType.STATE_TRANSITION]
    end_time: Optional[str] = None
    old_state: Optional[State] = None
    new_state: Optional[State] = None
    errors: Optional[List[str]] = None

class EngineStatusUpdateMetadata(RunEventMetadata):
    event_type: Literal[EventType.ENGINE_STATUS_UPDATE]
    # Add other fields as you discover them


class RunSubmittedToEngineMetadata(RunEventMetadata):
    event_type: Literal[EventType.RUN_SUBMITTED_TO_ENGINE]
    external_id: Optional[str] = None


RunEventMetadataUnion = Union[
    RunSubmittedMetadata,
    PreprocessingMetadata,
    ErrorOccurredMetadata,
    StateTransitionMetadata,
    EngineStatusUpdateMetadata,
    RunSubmittedToEngineMetadata,
    RunEventMetadata
]

class RunEvent(BaseModel):
    id: str
    event_type: EventType
    created_at: datetime
    metadata: RunEventMetadataUnion = Field(discriminator='event_type')


class ExtendedRunEvents(BaseModel):
    events: Optional[List[RunEvent]] = None

class ExtendedRun(BaseModel):
    run_id: str
    external_id: Optional[str] = None
    engine_id: Optional[str] = None
    request: Optional[ExtendedRunRequest] = None
    state: Optional[State] = None
    run_log: Optional[Log] = None
    errors: Optional[List[str]] = None
    task_logs: Optional[List[Log]] = None
    task_logs_url: Optional[str] = None
    outputs: Optional[Dict] = None
    dependencies: Optional[List[RunDependency]] = None
    events: Optional[List[RunEvent]] = None



class MinimalExtendedRun(BaseModel):
    run_id: Optional[str] = None
    state: Optional[State] = None
    msg: Optional[str] = None
    error_code: Optional[int] = None
    timestamp: Optional[str] = None
    trace_id: Optional[str] = None


class MinimalExtendedRunWithInputs(BaseModel):
    run_id: str
    inputs: Optional[Dict] = None


class MinimalExtendedRunWithOutputs(BaseModel):
    run_id: str
    outputs: Optional[Dict] = None


class BatchRunRequest(BaseModel):
    workflow_url: str
    workflow_type: Optional[str] = None
    workflow_type_version: Optional[str] = None
    engine_id: Optional[str] = None
    default_workflow_params: Optional[Dict] = None
    default_workflow_engine_parameters: Optional[Dict] = None
    default_tags: Optional[Dict] = None
    run_requests: Optional[List[ExtendedRunRequest]] = None
    samples: Optional[List[SimpleSample]] = None


class BatchRunResponse(BaseModel):
    runs: List[MinimalExtendedRun]


class RunId(BaseModel):
    run_id: str
    state: Optional[State] = None


class WorkbenchApiError(BaseModel):
    timestamp: Optional[str] = None
    msg: Optional[str] = None
    error_code: Optional[int] = None
    trace_id: Optional[str] = None


class ActionResult(BaseModel):
    outcome: Outcome
    data: Optional[Any] = None
    exception: Optional[WorkbenchApiError] = None


class BatchActionResult(BaseModel):
    results: List[ActionResult]


class TaskListResponse(PaginatedResource):
    tasks: List[Log]

    def items(self) -> List[Any]:
        return self.tasks


class ExtendedRunListResponse(PaginatedResource):
    runs: List[ExtendedRunStatus]

    def items(self) -> List[Any]:
        return self.runs


class ExtendedRunListOptions(BaseListOptions):
    expand: Optional[bool] = None
    until: Optional[str] = None
    since: Optional[str] = None
    search: Optional[str] = None
    sort: Optional[str] = None
    order: Optional[str] = Field(deprecated=True, default=None, json_schema_extra={'type': 'string'})
    direction: Optional[str] = None
    batch_id: Optional[str] = None
    state: Optional[List[State]] = None
    engine_id: Optional[str] = None
    submitted_by: Optional[str] = None
    workflow_name: Optional[str] = None
    workflow_version: Optional[str] = None
    workflow_url: Optional[str] = None
    workflow_type: Optional[str] = None
    workflow_type_version: Optional[str] = None
    tag: Optional[List[str]] = None
    sample_ids: Optional[List[str]] = None
    storage_account_id: Optional[str] = None
    show_hidden: Optional[bool] = False


class TaskListOptions(BaseListOptions):
    pass


class RunEventListOptions(BaseListOptions):
    run_id: str


class ExecutionEngineProviderType(str, Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    GCP = "GCP"
    LOCAL = "LOCAL"


class ExecutionEngine(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    provider: ExecutionEngineProviderType
    region: Optional[str] = None
    default: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    state: Optional[str] = None
    health: Optional[str] = Field(default=None, deprecated=True)
    engine_adapter_configuration: Optional[Dict[str, JSONType]] = None


class ExecutionEngineListResponse(PaginatedResource):
    engines: List[ExecutionEngine]

    def items(self) -> List[ExecutionEngine]:
        return self.engines


class ExecutionEngineListOptions(BaseListOptions):
    pass


class EngineParamPreset(BaseModel):
    id: str
    name: str
    default: Optional[bool] = None
    preset_values: Dict[str, object]
    engine_id: str
    etag: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class EngineParamPresetListResponse(PaginatedResource):
    engine_param_presets: List[EngineParamPreset]

    def items(self) -> List[EngineParamPreset]:
        return self.engine_param_presets


class EngineParamPresetListOptions(BaseListOptions):
    pass


class CheckType(str, Enum):
    CONNECTIVITY = 'CONNECTIVITY'
    CREDENTIALS = 'CREDENTIALS'
    PERMISSIONS = 'PERMISSIONS'
    STORAGE = 'STORAGE'
    LOGS = 'LOGS'


class Check(BaseModel):
    type: CheckType
    outcome: Outcome
    error: Optional[str] = None


class EngineHealthCheck(BaseModel):
    created_at: Optional[datetime] = None
    outcome: str
    checks: List[Check]
    

class EngineHealthCheckListResponse(PaginatedResource):
    health_checks: List[EngineHealthCheck]

    def items(self) -> List[EngineHealthCheck]:
        return self.health_checks


class EngineHealthCheckListOptions(BaseListOptions):
    outcome: Optional[str] = None
    check_type: Optional[str] = None
    sort: Optional[str] = None
