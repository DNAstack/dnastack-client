from typing import Optional, List, Dict, Any

from pydantic import BaseModel

from dnastack.client.workbench.models import PaginatedResource, BaseListOptions
from dnastack.client.workbench.workflow.models import WorkflowVersion


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
