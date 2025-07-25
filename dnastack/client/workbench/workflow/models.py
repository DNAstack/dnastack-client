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
    errors: Optional[Any]


class WorkflowVersion(BaseModel):
    workflowId: Optional[str]
    id: str
    externalId: Optional[str]
    versionName: str
    workflowName: str
    createdAt: Optional[str]
    lastUpdatedAt: Optional[str]
    descriptorType: str
    authors: Optional[List[str]] = None
    description: Optional[str] = None
    deleted: Optional[bool] = None
    etag: Optional[str] = None


class Workflow(BaseModel):
    internalId: str
    source: str
    name: str
    description: Optional[str]
    lastUpdatedAt: Optional[str]
    latestVersion: str
    authors: Optional[List[str]]
    versions: Optional[List[WorkflowVersion]]
    deleted: Optional[bool]
    etag: Optional[str]
    labels: Optional[List[str]]


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
    search: Optional[str]
    source: Optional[WorkflowSource]
    deleted: Optional[bool]
    sort: Optional[str]
    order: Optional[str] = Field(default=None, deprecated=True)
    direction: Optional[str]


class WorkflowListResponse(PaginatedResource):
    workflows: List[Workflow]

    def items(self) -> List[Any]:
        return self.workflows


class WorkflowVersionListOptions(BaseListOptions):
    deleted: Optional[bool]


class WorkflowVersionListResponse(PaginatedResource):
    versions: List[WorkflowVersion]

    def items(self) -> List[Any]:
        return self.versions

class ResolvedWorkflow(BaseModel):
    id: str
    internalId: str
    source: str
    name: str
    description: Optional[str]
    lastUpdatedAt: Optional[str]
    versionId: Optional[str]
    version: Optional[WorkflowVersion]
    authors: Optional[List[str]]
    etag: Optional[str]

class WorkflowDefaultsSelector(BaseModel):
    engine: Optional[str]
    provider: Optional[str]
    region: Optional[str]


class WorkflowDefaults(BaseModel):
    id: Optional[str]
    name: Optional[str]
    workflow_id: Optional[str]
    workflow_version_id: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    selector: Optional[WorkflowDefaultsSelector]
    values: Optional[Dict]
    etag: Optional[str]


class WorkflowDefaultsCreateRequest(BaseModel):
    id: Optional[str]
    name: Optional[str]
    selector: Optional[WorkflowDefaultsSelector]
    values: Optional[Dict]


class WorkflowDefaultsUpdateRequest(BaseModel):
    name: Optional[str]
    selector: Optional[WorkflowDefaultsSelector]
    values: Optional[Dict]


class WorkflowDefaultsListResponse(PaginatedResource):
    defaults: List[WorkflowDefaults]

    def items(self) -> List[WorkflowDefaults]:
        return self.defaults


class WorkflowDefaultsListOptions(BaseListOptions):
    sort: Optional[str]


class WorkflowTransformationCreate(BaseModel):
    id: Optional[str]
    next_transformation_id: Optional[str]
    script: Optional[str]
    labels: Optional[List[str]]


class WorkflowTransformation(BaseModel):
    id: Optional[str]
    workflow_id: Optional[str]
    workflow_version_id: Optional[str]
    next_transformation_id: Optional[str]
    script: Optional[str]
    labels: Optional[List[str]]
    created_at: Optional[str]


class WorkflowTransformationListOptions(BaseListOptions):
    pass


class WorkflowTransformationListResponse(PaginatedResource):
    transformations: List[WorkflowTransformation]

    def items(self) -> List[Any]:
        return self.transformations


class WorkflowDependencyPrerequisite(BaseModel):
    workflow_id: Optional[str]
    workflow_version_id: Optional[str]


class WorkflowDependency(BaseModel):
    namespace: Optional[str]
    id: Optional[str]
    workflow_id: Optional[str]
    workflow_version_id: Optional[str]
    name: Optional[str]
    dependencies: Optional[List[WorkflowDependencyPrerequisite]] = []
    global_: Optional[bool] = Field(default=None, alias="global")
    created_at: Optional[str]
    updated_at: Optional[str]


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
