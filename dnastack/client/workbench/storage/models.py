from typing import Optional, List, Any, Literal, Union

from pydantic import BaseModel

from dnastack.client.workbench.common.models import CaseInsensitiveEnum
from dnastack.client.workbench.models import BaseListOptions
from dnastack.client.workbench.models import PaginatedResource


class Provider(str, CaseInsensitiveEnum):
    aws = "aws"
    gcp = "gcp"
    azure = "azure"


class PlatformType(str, CaseInsensitiveEnum):
    pacbio = "pacbio"
    custom = "custom"


class AwsStorageAccountCredentials(BaseModel):
    type: Literal['AWS_ACCESS_KEY'] = 'AWS_ACCESS_KEY'
    access_key_id: Optional[str] = None
    secret_access_key: Optional[str] = None
    region: Optional[str] = None


class GcpStorageAccountCredentials(BaseModel):
    type: Literal['GCP_SERVICE_ACCOUNT'] = 'GCP_SERVICE_ACCOUNT'
    service_account_json: Optional[str] = None
    region: Optional[str] = None
    project_id: Optional[str] = None


class AzureCredentialsType(str, CaseInsensitiveEnum):
    SAS_URL = "SAS_URL"
    ACCESS_KEY = "ACCESS_KEY"
    CLIENT_CREDENTIALS = "CLIENT_CREDENTIALS"


class AzureStorageAccountCredentials(BaseModel):
    type: Literal['AZURE_CREDENTIALS'] = 'AZURE_CREDENTIALS'
    sas_url: Optional[str] = None
    access_key: Optional[str] = None
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    storage_account_name: Optional[str] = None
    azure_credentials_type: Optional[AzureCredentialsType] = None


class StorageAccount(BaseModel):
    id: Optional[str] = None
    namespace: Optional[str] = None
    name: Optional[str] = None
    etag: Optional[str] = None
    provider: Optional[Provider] = None
    created_at: Optional[str] = None
    last_updated_at: Optional[str] = None
    bucket: Optional[str] = None
    credentials: Optional[Union[AwsStorageAccountCredentials, GcpStorageAccountCredentials, AzureStorageAccountCredentials]]


class StorageListOptions(BaseListOptions):
    provider: Optional[Provider] = None
    sort: Optional[str] = None


class StorageListResponse(PaginatedResource):
    accounts: List[StorageAccount]

    def items(self) -> List[Any]:
        return self.accounts

