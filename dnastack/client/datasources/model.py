from typing import Optional

from pydantic.main import BaseModel

class DataSourceListOptions(BaseModel):
    pass

class DataSource(BaseModel):
    id: Optional[str]
    name: Optional[str]
    type: Optional[str]