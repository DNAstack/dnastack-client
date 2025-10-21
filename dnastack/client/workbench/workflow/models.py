from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any, List

from pydantic import BaseModel, Field

from dnastack.client.workbench.models import BaseListOptions, PaginatedResource


class WorkflowDescriptor(BaseModel):
    workflow_name: str
    input_schema: Dict
    output_schema: Dict
    wdl_version: str
    errors: Optional[Any] = None


class WorkflowVersion(BaseModel):
    workflowId: Optional[str] = None
    id: str
    externalId: Optional[str] = None
    versionName: str
    workflowName: str
    createdAt: Optional[str] = None
    lastUpdatedAt: Optional[str] = None
    descriptorType: str
    authors: Optional[List[str]] = None
    description: Optional[str] = None
    deleted: Optional[bool] = None
    etag: Optional[str] = None


class Workflow(BaseModel):
    internalId: str
    source: str
    name: str
    description: Optional[str] = None
    lastUpdatedAt: Optional[str] = None
    latestVersion: str
    authors: Optional[List[str]] = None
    versions: Optional[List[WorkflowVersion]] = None
    deleted: Optional[bool] = None
    etag: Optional[str] = None
    labels: Optional[List[str]] = None


class WorkflowFileType(str, Enum):
    primary = "PRIMARY_DESCRIPTOR"
    secondary = "DESCRIPTOR"
    test_file = "TEST_FILE"
    other = "OTHER"


class WorkflowSource(str, Enum):
    dockstore = "DOCKSTORE"
    custom = "CUSTOM"
    private = "PRIVATE"


class WorkflowFile(BaseModel):
    path: str
    file_type: WorkflowFileType
    base64_content: Optional[str] = None
    content: Optional[str] = None
    file_url: Optional[str] = None
    content_type: Optional[str] = None


class WorkflowCreate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    organization: Optional[str] = None
    version_name: Optional[str] = None
    entrypoint: str
    files: List[Path]
    labels: Optional[str] = None


class WorkflowVersionCreate(BaseModel):
    version_name: str
    entrypoint: str
    files: List[Path]


class WorkflowListOptions(BaseListOptions):
    search: Optional[str] = None
    source: Optional[WorkflowSource] = None
    deleted: Optional[bool] = None
    sort: Optional[str] = None
    order: Optional[str] = Field(default=None, deprecated=True)
    direction: Optional[str] = None


class WorkflowListResponse(PaginatedResource):
    workflows: List[Workflow]

    def items(self) -> List[Any]:
        return self.workflows


class WorkflowVersionListOptions(BaseListOptions):
    deleted: Optional[bool] = None


class WorkflowVersionListResponse(PaginatedResource):
    versions: List[WorkflowVersion]

    def items(self) -> List[Any]:
        return self.versions

class ResolvedWorkflow(BaseModel):
    id: str
    internalId: str
    source: str
    name: str
    description: Optional[str] = None
    lastUpdatedAt: Optional[str] = None
    versionId: Optional[str] = None
    version: Optional[WorkflowVersion] = None
    authors: Optional[List[str]] = None
    etag: Optional[str] = None

class WorkflowDefaultsSelector(BaseModel):
    engine: Optional[str] = None
    provider: Optional[str] = None
    region: Optional[str] = None


class WorkflowDefaults(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_version_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    selector: Optional[WorkflowDefaultsSelector] = None
    values: Optional[Dict] = None
    etag: Optional[str] = None


class WorkflowDefaultsCreateRequest(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    selector: Optional[WorkflowDefaultsSelector] = None
    values: Optional[Dict] = None


class WorkflowDefaultsUpdateRequest(BaseModel):
    name: Optional[str] = None
    selector: Optional[WorkflowDefaultsSelector] = None
    values: Optional[Dict] = None


class WorkflowDefaultsListResponse(PaginatedResource):
    defaults: List[WorkflowDefaults]

    def items(self) -> List[WorkflowDefaults]:
        return self.defaults


class WorkflowDefaultsListOptions(BaseListOptions):
    sort: Optional[str] = None


class WorkflowTransformationCreate(BaseModel):
    id: Optional[str] = None
    next_transformation_id: Optional[str] = None
    script: Optional[str] = None
    labels: Optional[List[str]] = None


class WorkflowTransformation(BaseModel):
    id: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_version_id: Optional[str] = None
    next_transformation_id: Optional[str] = None
    script: Optional[str] = None
    labels: Optional[List[str]] = None
    created_at: Optional[str] = None


class WorkflowTransformationListOptions(BaseListOptions):
    pass


class WorkflowTransformationListResponse(PaginatedResource):
    transformations: List[WorkflowTransformation]

    def items(self) -> List[Any]:
        return self.transformations


class WorkflowDependencyPrerequisite(BaseModel):
    workflow_id: Optional[str] = None
    workflow_version_id: Optional[str] = None


class WorkflowDependency(BaseModel):
    namespace: Optional[str] = None
    id: Optional[str] = None
    workflow_id: Optional[str] = None
    workflow_version_id: Optional[str] = None
    name: Optional[str] = None
    dependencies: Optional[List[WorkflowDependencyPrerequisite]] = []
    global_: Optional[bool] = Field(default=None, alias="global")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class WorkflowDependencyCreateRequest(BaseModel):
    name: str
    dependencies: List[WorkflowDependencyPrerequisite] = []


class WorkflowDependencyUpdateRequest(BaseModel):
    name: str
    dependencies: List[WorkflowDependencyPrerequisite] = []


class WorkflowDependencyListOptions(BaseListOptions):
    pass


class WorkflowDependencyListResponse(PaginatedResource):
    dependencies: Optional[List[WorkflowDependency]] = []

    def items(self) -> List[WorkflowDependency]:
        return self.dependencies or []
