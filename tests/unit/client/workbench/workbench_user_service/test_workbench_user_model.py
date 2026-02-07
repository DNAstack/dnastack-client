from dnastack.client.workbench.workbench_user_service.models import WorkbenchUser


class TestWorkbenchUserDeserialization:
    """Test suite for WorkbenchUser model deserialization."""

    def test_deserializes_with_all_fields(self):
        """WorkbenchUser should deserialize when all fields are present."""
        data = {
            "email": "alison@example.com",
            "full_name": "Alison Smith",
            "default_namespace": "alison-namespace",
        }
        user = WorkbenchUser(**data)
        assert user.email == "alison@example.com"
        assert user.full_name == "Alison Smith"
        assert user.default_namespace == "alison-namespace"

    def test_deserializes_with_null_full_name(self):
        """WorkbenchUser should accept None for full_name, as the API may return null
        for users who have not set their name."""
        data = {
            "email": "alison@example.com",
            "full_name": None,
            "default_namespace": "alison-namespace",
        }
        user = WorkbenchUser(**data)
        assert user.email == "alison@example.com"
        assert user.full_name is None
        assert user.default_namespace == "alison-namespace"

    def test_deserializes_with_missing_full_name(self):
        """WorkbenchUser should handle full_name being absent from the response."""
        data = {
            "email": "alison@example.com",
            "default_namespace": "alison-namespace",
        }
        user = WorkbenchUser(**data)
        assert user.email == "alison@example.com"
        assert user.full_name is None
        assert user.default_namespace == "alison-namespace"
