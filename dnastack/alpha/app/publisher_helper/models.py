from abc import ABC
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BaseItemInfo(BaseModel, ABC):
    """Base Simplified Library Item

    Based on https://github.com/DNAstack/indexing-service/blob/main/src/main/java/com/dnastack/indexingservice/library/LibraryItem.java.
    """

    id: str
    name: str
    type: str
    size: int
    size_unit: str
    item_updated_time: datetime

    def __hash__(self):
        return hash((self.id, self.name, self.type, self.size, self.size_unit, self.item_updated_time))

    def __eq__(self, other):
        if not isinstance(other, BaseItemInfo):
            return False
        return (self.id, self.name, self.type, self.size, self.size_unit, self.item_updated_time) == (
            other.id,
            other.name,
            other.type,
            other.size,
            other.size_unit,
            other.item_updated_time,
        )


class TableInfo(BaseItemInfo):
    """Simplified Library Item"""

    json_schema: Dict[str, Any]

    def __hash__(self):
        return hash((super().__hash__(), frozenset(self.json_schema.items())))

    def __eq__(self, other):
        if not isinstance(other, TableInfo):
            return False
        return super().__eq__(other) and self.json_schema == other.json_schema


class BlobInfo(BaseItemInfo):
    """Simplified Library Item"""

    checksums: Optional[List[Dict[str, str]]] = Field(default_factory=list)

    def __hash__(self):
        # Convert list of dicts to a frozenset of frozensets to ensure hashability
        checksums_frozenset = frozenset(frozenset(d.items()) for d in self.checksums)
        return hash((super().__hash__(), checksums_frozenset))

    def __eq__(self, other):
        if not isinstance(other, BlobInfo):
            return False
        return super().__eq__(other) and self.checksums == other.checksums


class ItemType(str, Enum):
    BLOB = "blob"
    TABLE = "table"
