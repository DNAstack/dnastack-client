from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel

from dnastack.client.workbench.common.models import State, CaseInsensitiveEnum
from dnastack.client.workbench.models import BaseListOptions, PaginatedResource
from dnastack.client.workbench.storage.models import PlatformType


class OntologyClass(BaseModel):
    id: str
    label: Optional[str] = None


class PhenotypicFeature(BaseModel):
    created_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    type: Optional[OntologyClass] = None


class SampleMetrics(BaseModel):
    file_count: Optional[int] = None
    instrument_types: Optional[List[str]] = None


class RunMetadata(BaseModel):
    run_id: Optional[str] = None
    state: Optional[State] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None
    submitted_by: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_version_id: Optional[str] = None
    workflow_name: Optional[str] = None
    workflow_version: Optional[str] = None
    last_recorded_event_time: Optional[datetime] = None
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
    id: Optional[List[str]] = None
    sexes: Optional[List[Sex]] = None
    search: Optional[str] = None
    since: Optional[str] = None
    until: Optional[str] = None
    perspective: Optional[PerspectiveType] = None


class SampleFile(BaseModel):
    sample_id: str
    path: str
    storage_account_id: Optional[str] = None
    platform_type: Optional[PlatformType] = None
    instrument_id: Optional[str] = None
    created_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    size: Optional[int] = None


class Sample(BaseModel):
    id: str
    created_at: Optional[datetime] = None
    last_updated_at: Optional[datetime] = None
    father_id: Optional[str] = None
    mother_id: Optional[str] = None
    family_id: Optional[str] = None
    sex: Optional[str] = None
    metrics: Optional[SampleMetrics] = None
    phenotypes: Optional[List[PhenotypicFeature]] = None
    runs: Optional[List[RunMetadata]] = None
    affected_status: Optional[AffectedStatus] = None
    has_been_analyzed: Optional[bool] = None


class SampleListResponse(PaginatedResource):
    samples: List[Sample]

    def items(self) -> List[Any]:
        return self.samples


class SampleFilesListOptions(BaseListOptions):
    storage_id: Optional[str] = None
    platform_type: Optional[PlatformType] = None
    instrument_id: Optional[str] = None
    search: Optional[str] = None


class SampleFileListResponse(PaginatedResource):
    files: List[SampleFile]

    def items(self) -> List[Any]:
        return self.files


class InstrumentListOptions(BaseListOptions):
    platform_type: Optional[PlatformType] = None


class Instrument(BaseModel):
    id: str
    platform_type: PlatformType


class InstrumentListResponse(PaginatedResource):
    instruments: List[Instrument]

    def items(self) -> List[Any]:
        return self.instruments
