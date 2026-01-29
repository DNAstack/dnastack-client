"""Unit tests for Hook model deserialization"""
import pytest
from datetime import datetime, timezone

from dnastack.client.workbench.ewes.models import Hook, HookListResponse


class TestHookDeserialization:
    """Tests for Hook model deserialization"""

    def test_hook_full_fields(self):
        """Test deserializing a hook with all fields populated"""
        data = {
            "id": "hook-123",
            "type": "LAUNCH_RUN",
            "state": "COMPLETE",
            "config": {"run_request": {"workflow_url": "my-workflow"}},
            "result_data": {"child_run_id": "run-456"},
            "created_at": "2026-01-15T10:00:00Z",
            "started_at": "2026-01-15T10:01:00Z",
            "finished_at": "2026-01-15T10:05:00Z",
            "updated_at": "2026-01-15T10:05:00Z",
        }
        hook = Hook(**data)
        assert hook.id == "hook-123"
        assert hook.type == "LAUNCH_RUN"
        assert hook.state == "COMPLETE"
        assert hook.config == {"run_request": {"workflow_url": "my-workflow"}}
        assert hook.result_data == {"child_run_id": "run-456"}
        assert hook.created_at is not None
        assert hook.started_at is not None
        assert hook.finished_at is not None
        assert hook.updated_at is not None

    def test_hook_minimal_fields(self):
        """Test deserializing a hook with only optional fields"""
        data = {}
        hook = Hook(**data)
        assert hook.id is None
        assert hook.type is None
        assert hook.state is None
        assert hook.config is None
        assert hook.result_data is None

    def test_hook_pending_state(self):
        """Test deserializing a hook in PENDING state with no result data"""
        data = {
            "id": "hook-789",
            "type": "INGEST_VARIANTS",
            "state": "PENDING",
            "config": {"ingest_to_publisher": True},
            "result_data": None,
            "created_at": "2026-01-15T10:00:00Z",
            "started_at": None,
            "finished_at": None,
            "updated_at": "2026-01-15T10:00:00Z",
        }
        hook = Hook(**data)
        assert hook.id == "hook-789"
        assert hook.type == "INGEST_VARIANTS"
        assert hook.state == "PENDING"
        assert hook.started_at is None
        assert hook.finished_at is None

    def test_hook_failed_state(self):
        """Test deserializing a hook in FAILED state"""
        data = {
            "id": "hook-fail",
            "type": "LAUNCH_RUN",
            "state": "FAILED",
            "config": {"run_request": {}},
            "result_data": None,
            "created_at": "2026-01-15T10:00:00Z",
            "started_at": "2026-01-15T10:01:00Z",
            "finished_at": "2026-01-15T10:02:00Z",
            "updated_at": "2026-01-15T10:02:00Z",
        }
        hook = Hook(**data)
        assert hook.state == "FAILED"


class TestHookListResponseDeserialization:
    """Tests for HookListResponse model deserialization"""

    def test_hook_list_response_with_hooks(self):
        """Test deserializing a list response with hooks"""
        data = {
            "hooks": [
                {"id": "hook-1", "type": "LAUNCH_RUN", "state": "COMPLETE"},
                {"id": "hook-2", "type": "INGEST_VARIANTS", "state": "PENDING"},
            ],
            "pagination": None,
        }
        response = HookListResponse(**data)
        assert len(response.hooks) == 2
        assert response.hooks[0].id == "hook-1"
        assert response.hooks[1].id == "hook-2"

    def test_hook_list_response_empty(self):
        """Test deserializing a list response with no hooks"""
        data = {
            "hooks": [],
            "pagination": None,
        }
        response = HookListResponse(**data)
        assert len(response.hooks) == 0

    def test_hook_list_response_null_hooks(self):
        """Test deserializing a list response with null hooks"""
        data = {
            "hooks": None,
            "pagination": None,
        }
        response = HookListResponse(**data)
        assert response.hooks is None
