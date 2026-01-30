from typing import Optional

from pydantic import BaseModel


class WorkbenchUser(BaseModel):
    email: str
    full_name: Optional[str] = None
    default_namespace: str
