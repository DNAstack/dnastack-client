from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TenantStatus(str, Enum):
    """ Whether a tenant is accessible. A disabled tenant keeps its data but none of it can be reached. """
    ENABLED = 'ENABLED'
    DISABLED = 'DISABLED'


class Tenant(BaseModel):
    """ A Publisher tenant, as managed by wallet """
    id: Optional[str] = None
    name: str
    status: Optional[TenantStatus] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    """ When the tenant expires and is deleted, or None if it never expires """
