import re
from datetime import datetime
from enum import Enum
from time import time
from typing import Optional, List, Any, Dict

from pydantic import BaseModel, Field

from dnastack.client.base_exceptions import ApiError


class Tag(BaseModel):
    id: Optional[str] = None
    label: str


COLLECTION_READ_ONLY_PROPERTIES = (
    'id',
    'itemsQuery',
    'tags',
    'createdAt',
    'updatedAt',
    'dbSchemaName',
    'itemsChangedAt',
    'latestItemUpdatedTime',
    'accessTypeLabels',
    'itemCounts',
)


class Collection(BaseModel):
    """
    A model representing a collection

    .. note:: This is not a full representation of the object.
    """

    id: Optional[str] = None
    name: str
    slugName: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    description: Optional[str] = None
    itemsQuery: Optional[str] = None
    tags: Optional[List[Tag]] = Field(default_factory=list)
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    dbSchemaName: Optional[str] = None
    itemsChangedAt: Optional[datetime] = None
    latestItemUpdatedTime: Optional[datetime] = None
    accessTypeLabels: Optional[Dict[str, str]] = None
    itemCounts: Optional[Dict[str, int]] = Field(default_factory=dict)

    @classmethod
    def make(cls,
             name: str,
             items_query: str,
             slug_name: Optional[str] = None,
             description: Optional[str] = None):
        if not slug_name:
            slug_name = re.sub(r'[^a-z0-9-]', '-', name.lower()) + str(int(time()))
            slug_name = re.sub(r'-+', '-', slug_name)
        return cls(name=name, itemsQuery=items_query, slugName=slug_name, description=description)


class PageableApiError(ApiError):
    def __init__(self, message, status_code, text, urls):
        super().__init__(message, status_code, text)
        self.urls = urls


class Pagination(BaseModel):
    nextPageUrl: Optional[str] = None


class PaginatedResource(BaseModel):
    pagination: Optional[Pagination] = None

    def items(self) -> List[Any]:
        pass

class CollectionItem(BaseModel):
    id: str
    collectionId: Optional[str] = None
    type: Optional[str] = None
    name: Optional[str] = None
    displayName: Optional[str] = None
    dataSourceName: Optional[str] = None
    dataSourceType: Optional[str] = None
    cachedAt: Optional[str] = None
    createdTime: Optional[str] = None
    updatedTime: Optional[str] = None
    itemUpdatedTime: Optional[str] = None
    sourceKey: Optional[str] = None
    metadataUrl: Optional[str] = None
    dataSourceUrl: Optional[str] = None
    sizeUnit: Optional[str] = None
    size: Optional[int] = None


class CollectionItemListResponse(BaseModel):
    items: List[CollectionItem]
    pagination: Optional[Pagination] = None


class CollectionItemListOptions(BaseModel):
    type: Optional[str] = None
    limit: Optional[int] = None
    onlyMissing: Optional[bool] = None


class CreateCollectionItemsRequest(BaseModel):
    dataSourceId: str
    dataSourceType: Optional[str] = None
    sourceKeys: List[str]


class DeleteCollectionItemRequest(BaseModel):
    dataSourceId: str
    dataSourceType: Optional[str] = None
    sourceKey: str


class CollectionValidationStatus(str, Enum):
    VALIDATED = 'VALIDATED'
    VALIDATION_STOPPED = 'VALIDATION_STOPPED'
    VALIDATION_IN_PROGRESS = 'VALIDATION_IN_PROGRESS'
    MISSING_ITEMS = 'MISSING_ITEMS'


class CollectionValidationMissingItems(BaseModel):
    files: Optional[int] = None
    tables: Optional[int] = None


class CollectionStatus(BaseModel):
    validationsStatus: CollectionValidationStatus
    lastChecked: Optional[datetime] = None
    missingItems: Optional[int] = None
