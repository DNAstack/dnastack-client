from typing import Any, ClassVar, List, Optional

from pydantic import BaseModel

from dnastack.client.workbench.models import PaginatedResource


class WorkbenchUser(BaseModel):
    email: str
    full_name: Optional[str] = None
    default_namespace: str


class Namespace(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


class NamespaceListResponse(PaginatedResource):
    namespaces: List[Namespace]

    def items(self) -> List[Any]:
        return self.namespaces


class NamespaceMember(BaseModel):
    user_id: str
    email: str
    full_name: Optional[str] = None
    role: str
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    updated_at: Optional[str] = None


class AddMemberRequest(BaseModel):
    email: Optional[str] = None
    id: Optional[str] = None
    role: str


class InitialUser(BaseModel):
    ROLE_ADMIN: ClassVar[str] = "ADMIN"

    email: str
    role: str


class NamespaceCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    initial_users: Optional[List[InitialUser]] = None


class NamespaceMemberListResponse(PaginatedResource):
    members: List[NamespaceMember]

    def items(self) -> List[Any]:
        return self.members
