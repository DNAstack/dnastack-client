from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Literal, Union

from pydantic import BaseModel, Field

from dnastack.client.service_registry.models import Service
from dnastack.client.workbench.models import BaseListOptions, PaginatedResource
from dnastack.client.workbench.samples.models import Sample
from dnastack.common.json_argument_parser import JSONType


class Outcome(str, Enum):
    SUCCESS = 'SUCCESS',
    FAILURE = 'FAILURE'


class LogType(str, Enum):
    STDOUT = 'stdout',
    STDERR = 'stderr',


class State(str, Enum):
    PREPROCESSING = "PREPROCESSING"
    UNKNOWN = "UNKNOWN"
    QUEUED = "QUEUED"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CANCELING = "CANCELING"
    COMPLETE = "COMPLETE"
    EXECUTOR_ERROR = "EXECUTOR_ERROR"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    CANCELED = "CANCELED"
    COMPLETE_WITH_ERRORS = "COMPLETE_WITH_ERRORS"
    PREPROCESSING_ERROR = "PREPROCESSING_ERROR"

    def is_error(self) -> bool:
        return self in [State.COMPLETE_WITH_ERRORS, State.EXECUTOR_ERROR, State.SYSTEM_ERROR]

    def is_terminal(self) -> bool:
        return self in [State.COMPLETE, State.COMPLETE_WITH_ERRORS, State.CANCELED, State.EXECUTOR_ERROR,
                        State.SYSTEM_ERROR]


class WesServiceInfo(Service):
    workflow_type_versions: Optional[Dict]
    supported_wes_versions: Optional[List[str]]
    supported_filesystem_protocols: Optional[List[str]]
    workflow_engine_versions: Optional[Dict]
    default_workflow_engine_parameters: Optional[List[Dict]]
    system_state_counts: Optional[Dict]
    auth_instructions_url: Optional[str]
    tags: Optional[Dict]


class ExtendedRunStatus(BaseModel):
    run_id: str
    external_id: Optional[str]
    state: State
    start_time: datetime
    end_time: Optional[datetime]
    submitted_by: Optional[str]
    workflow_id: Optional[str]
    workflow_version_id: Optional[str]
    workflow_url: Optional[str]
    workflow_name: Optional[str]
    workflow_version: Optional[str]
    workflow_authors: Optional[List[str]]
    workflow_type: Optional[str]
    workflow_type_version: Optional[str]
    workflow_params: Optional[Dict]
    tags: Optional[Dict]
    workflow_engine_parameters: Optional[Dict]


class Log(BaseModel):
    task_id: Optional[str]
    name: str
    pretty_name: Optional[str]
    cmd: Optional[Any]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    stdout: Optional[str]
    stderr: Optional[str]
    exit_code: Optional[int]
    state: Optional[State]

class RunDependency(BaseModel):
    run_id: str

class ExtendedRunRequest(BaseModel):
    workflow_url: Optional[str]
    workflow_name: Optional[str]
    workflow_version: Optional[str]
    workflow_authors: Optional[List[str]]
    workflow_type: Optional[str]
    workflow_type_version: Optional[str]
    workflow_id: Optional[str]
    workflow_version_id: Optional[str]
    submitted_by: Optional[str]
    workflow_params: Optional[Dict]
    workflow_engine_parameters: Optional[Dict]
    dependencies: Optional[List[RunDependency]]
    tags: Optional[Dict]


class EventType(str, Enum):
    PREPROCESSING = "PREPROCESSING"
    RUN_SUBMITTED = "RUN_SUBMITTED"
    RUN_SUBMITTED_TO_ENGINE = "RUN_SUBMITTED_TO_ENGINE"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    ENGINE_STATUS_UPDATE = "ENGINE_STATUS_UPDATE"
    STATE_TRANSITION = "STATE_TRANSITION"

class SampleId(BaseModel):
    id: Optional[str]
    storage_account_id: Optional[str]

class RunEventMetadata(BaseModel):
    message: Optional[str]


class RunSubmittedMetadata(RunEventMetadata):
    event_type: Literal[EventType.RUN_SUBMITTED]
    start_time: Optional[str]
    submitted_by: Optional[str]
    state: Optional[State]
    workflow_id: Optional[str]
    workflow_version_id: Optional[str]
    workflow_url: Optional[str]
    workflow_name: Optional[str]
    workflow_version: Optional[str]
    workflow_authors: Optional[List[str]]
    workflow_type: Optional[str]
    workflow_type_version: Optional[str]
    tags: Optional[dict[str, str]]
    sample_ids: Optional[List[SampleId]]

class PreprocessingMetadata(RunEventMetadata):
    event_type: Literal[EventType.PREPROCESSING]
    outcome: Optional[str]

class ErrorOccurredMetadata(RunEventMetadata):
    event_type: Literal[EventType.ERROR_OCCURRED]
    errors: Optional[List[str]]

class StateTransitionMetadata(RunEventMetadata):
    event_type: Literal[EventType.STATE_TRANSITION]
    end_time: Optional[str]
    old_state: Optional[State]
    new_state: Optional[State]
    errors: Optional[List[str]]

class EngineStatusUpdateMetadata(RunEventMetadata):
    event_type: Literal[EventType.ENGINE_STATUS_UPDATE]
    # Add other fields as you discover them

class RunSubmittedToEngineMetadata(RunEventMetadata):
    event_type: Literal[EventType.RUN_SUBMITTED_TO_ENGINE]


RunEventMetadataUnion = Union[
    RunSubmittedMetadata,
    PreprocessingMetadata,
    ErrorOccurredMetadata,
    StateTransitionMetadata,
    EngineStatusUpdateMetadata,
    RunSubmittedToEngineMetadata
]

class RunEvent(BaseModel):
    id: str
    event_type: EventType
    created_at: datetime
    metadata: RunEventMetadataUnion = Field(discriminator='event_type')

class ExtendedRunEvents(BaseModel):
    events: Optional[List[RunEvent]]

class ExtendedRun(BaseModel):
    run_id: str
    external_id: Optional[str]
    engine_id: Optional[str]
    request: Optional[ExtendedRunRequest]
    state: Optional[State]
    run_log: Optional[Log]
    errors: Optional[List[str]]
    task_logs: Optional[List[Log]]
    task_logs_url: Optional[str]
    outputs: Optional[Dict]
    dependencies: Optional[List[RunDependency]]
    events: Optional[List[RunEvent]]



class MinimalExtendedRun(BaseModel):
    run_id: Optional[str]
    state: Optional[State]
    msg: Optional[str]
    error_code: Optional[int]
    timestamp: Optional[str]
    trace_id: Optional[str]


class MinimalExtendedRunWithInputs(BaseModel):
    run_id: str
    inputs: Optional[Dict]


class MinimalExtendedRunWithOutputs(BaseModel):
    run_id: str
    outputs: Optional[Dict]


class BatchRunRequest(BaseModel):
    workflow_url: str
    workflow_type: Optional[str]
    workflow_type_version: Optional[str]
    engine_id: Optional[str]
    default_workflow_params: Optional[Dict]
    default_workflow_engine_parameters: Optional[Dict]
    default_tags: Optional[Dict]
    run_requests: Optional[List[ExtendedRunRequest]]
    samples: Optional[List[Sample]]


class BatchRunResponse(BaseModel):
    runs: List[MinimalExtendedRun]


class RunId(BaseModel):
    run_id: str
    state: Optional[State]


class WorkbenchApiError(BaseModel):
    timestamp: Optional[str]
    msg: Optional[str]
    error_code: Optional[int]
    trace_id: Optional[str]


class ActionResult(BaseModel):
    outcome: Outcome
    data: Optional[Any]
    exception: Optional[WorkbenchApiError]


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
    expand: Optional[bool]
    until: Optional[str]
    since: Optional[str]
    search: Optional[str]
    sort: Optional[str]
    order: Optional[str] = Field(type=str, deprecated=True, default=None)
    direction: Optional[str]
    batch_id: Optional[str]
    state: Optional[List[State]]
    engine_id: Optional[str]
    submitted_by: Optional[str]
    workflow_name: Optional[str]
    workflow_version: Optional[str]
    workflow_url: Optional[str]
    workflow_type: Optional[str]
    workflow_type_version: Optional[str]
    tag: Optional[List[str]]


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
    description: Optional[str]
    provider: ExecutionEngineProviderType
    region: Optional[str]
    default: Optional[bool]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    state: Optional[str]
    health: Optional[str] = Field(default=None, deprecated=True)
    engine_adapter_configuration: Optional[Dict[str, JSONType]]


class ExecutionEngineListResponse(PaginatedResource):
    engines: List[ExecutionEngine]

    def items(self) -> List[ExecutionEngine]:
        return self.engines


class ExecutionEngineListOptions(BaseListOptions):
    pass


class EngineParamPreset(BaseModel):
    id: str
    name: str
    default: Optional[bool]
    preset_values: Dict[str, object]
    engine_id: str
    etag: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


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
    error: Optional[str]


class EngineHealthCheck(BaseModel):
    created_at: Optional[datetime]
    outcome: str
    checks: List[Check]
    

class EngineHealthCheckListResponse(PaginatedResource):
    health_checks: List[EngineHealthCheck]

    def items(self) -> List[EngineHealthCheck]:
        return self.health_checks


class EngineHealthCheckListOptions(BaseListOptions):
    outcome: Optional[str]
    check_type: Optional[str]
    sort: Optional[str]
