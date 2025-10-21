from typing import Optional

from pydantic.main import BaseModel

class DataSourceListOptions(BaseModel):
    pass

class DataSource(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    type: Optional[str] = None