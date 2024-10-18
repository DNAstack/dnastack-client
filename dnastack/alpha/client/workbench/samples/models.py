from datetime import datetime

from pydantic import BaseModel

from typing import List, Optional, Any

from dnastack.alpha.client.workbench.storage.models import Platform, PlatformType
from dnastack.client.workbench.models import BaseListOptions, PaginatedResource


class SampleListOptions(BaseListOptions):
    pass


class SampleFile(BaseModel):
    sample_id: str
    path: str
    storage_account_id: Optional[str]
    platform_id: Optional[str]
    platform_type: Optional[PlatformType]
    instrument_id: Optional[str]
    region: Optional[str]
    created_at: Optional[datetime]
    last_updated_at: Optional[datetime]




class Sample(BaseModel):
    id: str
    created_at: Optional[datetime]
    last_updated_at: Optional[datetime]
    files: Optional[List[SampleFile]]


class SampleListResponse(PaginatedResource):
    samples: List[Sample]

    def items(self) -> List[Any]:
        return self.samples

class SampleFilesListOptions(BaseListOptions):
    platform_id: Optional[str]
    storage_id: Optional[str]
    platform_type: Optional[PlatformType]
    instrument_id: Optional[str]
    search: Optional[str]

class SampleFileListResponse(PaginatedResource):
    files: List[SampleFile]

    def items(self) -> List[Any]:
        return self.files