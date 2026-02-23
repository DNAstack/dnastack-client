from dnastack.client.workbench.workbench_user_service.models import (
    Namespace,
    NamespaceMember,
    NamespaceListResponse,
    NamespaceMemberListResponse,
)


class TestNamespaceDeserialization:
    """Test suite for Namespace model deserialization."""

    def test_deserializes_with_all_fields(self):
        data = {
            "id": "bcd869ca-8a06-4426-a94d-43f9d91e937d",
            "name": "My Workspace",
            "description": "Workspace for test@example.com",
            "created_at": "2025-10-21T19:16:10.470916Z",
            "created_by": "UserDatabaseMigrationService",
            "updated_at": "2025-10-21T19:16:10.470916Z",
            "updated_by": "UserDatabaseMigrationService",
        }
        ns = Namespace(**data)
        assert ns.id == "bcd869ca-8a06-4426-a94d-43f9d91e937d"
        assert ns.name == "My Workspace"
        assert ns.description == "Workspace for test@example.com"
        assert ns.created_at == "2025-10-21T19:16:10.470916Z"
        assert ns.created_by == "UserDatabaseMigrationService"
        assert ns.updated_at == "2025-10-21T19:16:10.470916Z"
        assert ns.updated_by == "UserDatabaseMigrationService"

    def test_deserializes_with_optional_fields_missing(self):
        data = {
            "id": "abc123",
            "name": "Minimal Workspace",
        }
        ns = Namespace(**data)
        assert ns.id == "abc123"
        assert ns.name == "Minimal Workspace"
        assert ns.description is None
        assert ns.created_at is None
        assert ns.created_by is None
        assert ns.updated_at is None
        assert ns.updated_by is None

    def test_deserializes_with_null_optional_fields(self):
        data = {
            "id": "abc123",
            "name": "Test",
            "description": None,
            "created_by": None,
            "updated_by": None,
        }
        ns = Namespace(**data)
        assert ns.description is None
        assert ns.created_by is None
        assert ns.updated_by is None


class TestNamespaceMemberDeserialization:
    """Test suite for NamespaceMember model deserialization."""

    def test_deserializes_with_all_fields(self):
        data = {
            "user_id": "bcd869ca-8a06-4426-a94d-43f9d91e937d",
            "email": "patrick@dnastack.com",
            "full_name": "Patrick Magee",
            "role": "ADMIN",
            "created_at": "2026-02-18T20:24:18.229110Z",
            "created_by": "UserDatabaseMigrationService",
            "updated_at": "2026-02-18T20:24:18.229110Z",
        }
        member = NamespaceMember(**data)
        assert member.user_id == "bcd869ca-8a06-4426-a94d-43f9d91e937d"
        assert member.email == "patrick@dnastack.com"
        assert member.full_name == "Patrick Magee"
        assert member.role == "ADMIN"
        assert member.created_at == "2026-02-18T20:24:18.229110Z"
        assert member.created_by == "UserDatabaseMigrationService"
        assert member.updated_at == "2026-02-18T20:24:18.229110Z"

    def test_deserializes_with_null_full_name(self):
        data = {
            "user_id": "abc123",
            "email": "test@example.com",
            "full_name": None,
            "role": "MEMBER",
        }
        member = NamespaceMember(**data)
        assert member.full_name is None

    def test_deserializes_with_missing_optional_fields(self):
        data = {
            "user_id": "abc123",
            "email": "test@example.com",
            "role": "MEMBER",
        }
        member = NamespaceMember(**data)
        assert member.full_name is None
        assert member.created_at is None
        assert member.created_by is None
        assert member.updated_at is None


class TestNamespaceListResponseDeserialization:
    """Test suite for NamespaceListResponse deserialization."""

    def test_deserializes_response_with_items(self):
        data = {
            "namespaces": [
                {"id": "ns-1", "name": "Workspace 1"},
                {"id": "ns-2", "name": "Workspace 2"},
            ],
            "pagination": {"next_page_url": None, "total_elements": 2},
        }
        response = NamespaceListResponse(**data)
        assert len(response.items()) == 2
        assert response.items()[0].id == "ns-1"
        assert response.items()[1].name == "Workspace 2"
        assert response.pagination.total_elements == 2
        assert response.pagination.next_page_url is None

    def test_deserializes_empty_response(self):
        data = {
            "namespaces": [],
            "pagination": {"next_page_url": None, "total_elements": 0},
        }
        response = NamespaceListResponse(**data)
        assert len(response.items()) == 0

    def test_deserializes_response_with_next_page(self):
        data = {
            "namespaces": [{"id": "ns-1", "name": "Workspace 1"}],
            "pagination": {
                "next_page_url": "https://example.com/namespaces?page=2",
                "total_elements": 10,
            },
        }
        response = NamespaceListResponse(**data)
        assert len(response.items()) == 1
        assert response.pagination.next_page_url == "https://example.com/namespaces?page=2"


class TestNamespaceMemberListResponseDeserialization:
    """Test suite for NamespaceMemberListResponse deserialization."""

    def test_deserializes_response_with_items(self):
        data = {
            "members": [
                {"user_id": "u-1", "email": "a@example.com", "role": "ADMIN"},
                {"user_id": "u-2", "email": "b@example.com", "role": "MEMBER"},
            ],
            "pagination": {"next_page_url": None, "total_elements": 2},
        }
        response = NamespaceMemberListResponse(**data)
        assert len(response.items()) == 2
        assert response.items()[0].email == "a@example.com"
        assert response.items()[1].role == "MEMBER"

    def test_deserializes_empty_response(self):
        data = {
            "members": [],
            "pagination": {"next_page_url": None, "total_elements": 0},
        }
        response = NamespaceMemberListResponse(**data)
        assert len(response.items()) == 0

    def test_deserializes_response_with_next_page(self):
        data = {
            "members": [
                {"user_id": "u-1", "email": "a@example.com", "role": "ADMIN"},
            ],
            "pagination": {
                "next_page_url": "https://example.com/namespaces/ns-1/members?page=2",
                "total_elements": 5,
            },
        }
        response = NamespaceMemberListResponse(**data)
        assert response.pagination.next_page_url == "https://example.com/namespaces/ns-1/members?page=2"
