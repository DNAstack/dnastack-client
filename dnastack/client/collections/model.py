import re
from datetime import datetime
from enum import Enum
from time import time
from typing import Optional, List, Any, Dict

from pydantic import BaseModel, Field

from dnastack.client.base_exceptions import ApiError


class Tag(BaseModel):
    id: Optional[str]
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
    itemsQuery: Optional[str]
    tags: Optional[List[Tag]] = Field(default_factory=list)
    createdAt: Optional[datetime]
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
    nextPageUrl: Optional[str]


class PaginatedResource(BaseModel):
    pagination: Optional[Pagination]

    def items(self) -> List[Any]:
        pass

class CollectionItem(BaseModel):
    id: str
    collectionId: Optional[str]
    type: Optional[str]
    name: Optional[str]
    displayName: Optional[str]
    dataSourceName: Optional[str]
    dataSourceType: Optional[str]
    cachedAt: Optional[str]
    createdTime: Optional[str]
    updatedTime: Optional[str]
    itemUpdatedTime: Optional[str]
    sourceKey: Optional[str]
    metadataUrl: Optional[str]
    dataSourceUrl: Optional[str]
    sizeUnit: Optional[str]
    size: Optional[int]


class CollectionItemListResponse(BaseModel):
    items: List[CollectionItem]
    pagination: Optional[Pagination]


class CollectionItemListOptions(BaseModel):
    type: Optional[str]
    limit: Optional[int]


class CreateCollectionItemsRequest(BaseModel):
    dataSourceId: str
    dataSourceType: Optional[str]
    sourceKeys: List[str]


class DeleteCollectionItemRequest(BaseModel):
    dataSourceId: str
    dataSourceType: Optional[str]
    sourceKey: str


class CollectionValidationStatus(str, Enum):
    VALIDATED = 'VALIDATED'
    VALIDATION_STOPPED = 'VALIDATION_STOPPED'
    VALIDATION_IN_PROGRESS = 'VALIDATION_IN_PROGRESS'
    MISSING_ITEMS = 'MISSING_ITEMS'


class CollectionValidationMissingItems(BaseModel):
    files: Optional[int]
    tables: Optional[int]


class CollectionStatus(BaseModel):
    validationsStatus: CollectionValidationStatus
    lastChecked: Optional[datetime]
    missingItems: Optional[int]
