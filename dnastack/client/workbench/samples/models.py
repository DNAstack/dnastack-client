from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel

from dnastack.client.workbench.common.models import State, CaseInsensitiveEnum
from dnastack.client.workbench.models import BaseListOptions, PaginatedResource
from dnastack.client.workbench.storage.models import PlatformType


class OntologyClass(BaseModel):
    id: str
    label: Optional[str]


class PhenotypicFeature(BaseModel):
    created_at: Optional[datetime]
    last_updated_at: Optional[datetime]
    type: Optional[OntologyClass]


class SampleMetrics(BaseModel):
    file_count: Optional[int]
    instrument_types: Optional[List[str]]


class RunMetadata(BaseModel):
    run_id: Optional[str]
    state: Optional[State]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    updated_time: Optional[datetime]
    submitted_by: Optional[str]
    workflow_id: Optional[str]
    workflow_version_id: Optional[str]
    workflow_name: Optional[str]
    workflow_version: Optional[str]
    last_recorded_event_time: Optional[datetime]
    tags: Optional[dict[str, str]]


class Sex(str, CaseInsensitiveEnum):
    male = "MALE"
    female = "FEMALE"
    unknown_sex = "UNKNOWN_SEX"
    other_sex = "OTHER_SEX"


class AffectedStatus(str, CaseInsensitiveEnum):
    affected = "AFFECTED"
    unaffected = "UNAFFECTED"
    missing = "MISSING"


class PerspectiveType(str, CaseInsensitiveEnum):
    default = "DEFAULT"
    workflow = "WORKFLOW"


class SampleListOptions(BaseListOptions):
    storage_id: Optional[str] = None
    platform_type: Optional[PlatformType] = None
    instrument_id: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_version_id: Optional[str] = None
    states: Optional[List[State]] = None
    family_id: Optional[List[str]] = None
    sample_id: Optional[List[str]] = None
    sexes: Optional[List[Sex]] = None
    search: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None
    perspective: Optional[PerspectiveType] = None


class SampleFile(BaseModel):
    sample_id: str
    path: str
    storage_account_id: Optional[str]
    platform_type: Optional[PlatformType]
    instrument_id: Optional[str]
    created_at: Optional[datetime]
    last_updated_at: Optional[datetime]
    size: Optional[int]


class Sample(BaseModel):
    id: str
    created_at: Optional[datetime]
    last_updated_at: Optional[datetime]
    father_id: Optional[str]
    mother_id: Optional[str]
    family_id: Optional[str]
    sex: Optional[str]
    metrics: Optional[SampleMetrics]
    phenotypes: Optional[List[PhenotypicFeature]]
    runs: Optional[List[RunMetadata]]
    affected_status: Optional[AffectedStatus]
    has_been_analyzed: Optional[bool]


class SampleListResponse(PaginatedResource):
    samples: List[Sample]

    def items(self) -> List[Any]:
        return self.samples


class SampleFilesListOptions(BaseListOptions):
    storage_id: Optional[str]
    platform_type: Optional[PlatformType]
    instrument_id: Optional[str]
    search: Optional[str]


class SampleFileListResponse(PaginatedResource):
    files: List[SampleFile]

    def items(self) -> List[Any]:
        return self.files


class InstrumentListOptions(BaseListOptions):
    platform_type: Optional[PlatformType]


class Instrument(BaseModel):
    id: str
    platform_type: PlatformType


class InstrumentListResponse(PaginatedResource):
    instruments: List[Instrument]

    def items(self) -> List[Any]:
        return self.instruments
