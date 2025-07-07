from datetime import datetime
from typing import List, Optional, Any

from pydantic import BaseModel

from dnastack.client.workbench.models import BaseListOptions, PaginatedResource
from dnastack.client.workbench.storage.models import PlatformType


class SampleListOptions(BaseListOptions):
    pass


class SampleFile(BaseModel):
    sample_id: str
    path: str
    storage_account_id: Optional[str]
    platform_type: Optional[PlatformType]
    instrument_id: Optional[str]
    region: Optional[str]
    created_at: Optional[datetime]
    last_updated_at: Optional[datetime]


class Sample(BaseModel):
    id: str
    created_at: Optional[datetime]
    last_updated_at: Optional[datetime]


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
