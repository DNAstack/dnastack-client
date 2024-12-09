from enum import Enum
from typing import Optional, List, Any, Literal, Union

from pydantic import BaseModel

from dnastack.client.workbench.models import BaseListOptions
from dnastack.client.workbench.models import PaginatedResource


class CaseInsensitiveEnum(Enum):
    @classmethod
    def _missing_(cls, value):
        for member in cls:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f"{value} is not a valid {cls.__name__}")


class Provider(str, CaseInsensitiveEnum):
    aws = "aws"
    gcp = "gcp"
    azure = "azure"


class PlatformType(str, CaseInsensitiveEnum):
    pacbio = "pacbio"


class AwsStorageAccountCredentials(BaseModel):
    type: Literal['AWS_ACCESS_KEY'] = 'AWS_ACCESS_KEY'
    access_key_id: Optional[str]
    secret_access_key: Optional[str]
    region: Optional[str]


class GcpStorageAccountCredentials(BaseModel):
    type: Literal['GCP_SERVICE_ACCOUNT'] = 'GCP_SERVICE_ACCOUNT'
    service_account_json: Optional[str]
    region: Optional[str]
    project_id: Optional[str]


class AzureCredentialsType(str, CaseInsensitiveEnum):
    SAS_URL = "SAS_URL"
    ACCESS_KEY = "ACCESS_KEY"
    CLIENT_CREDENTIALS = "CLIENT_CREDENTIALS"


class AzureStorageAccountCredentials(BaseModel):
    type: Literal['AZURE_CREDENTIALS'] = 'AZURE_CREDENTIALS'
    sas_url: Optional[str]
    access_key: Optional[str]
    tenant_id: Optional[str]
    client_id: Optional[str]
    client_secret: Optional[str]
    storage_account_name: Optional[str]
    azure_credentials_type: Optional[AzureCredentialsType]


class StorageAccount(BaseModel):
    id: Optional[str]
    namespace: Optional[str]
    name: Optional[str]
    etag: Optional[str]
    provider: Optional[Provider]
    created_at: Optional[str]
    last_updated_at: Optional[str]
    bucket: Optional[str]
    credentials: Optional[Union[AwsStorageAccountCredentials, GcpStorageAccountCredentials, AzureStorageAccountCredentials]]


class StorageListOptions(BaseListOptions):
    provider: Optional[Provider]
    sort: Optional[str]


class StorageListResponse(PaginatedResource):
    accounts: List[StorageAccount]

    def items(self) -> List[Any]:
        return self.accounts

