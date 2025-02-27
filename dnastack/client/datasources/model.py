from pydantic.main import BaseModel, Field


class DataSource(BaseModel):
    """
    A model representing a data source
    """
    id: str = Field(..., description="Unique identifier of the data source")
    name: str = Field(..., description="Name of the data source")
    type: str = Field(..., description="Type of the data source")