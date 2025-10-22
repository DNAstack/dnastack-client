import json
import uuid
from datetime import datetime
from typing import Dict, Any

import pytest
from pydantic import ValidationError

from dnastack.client.workbench.ewes.models import (
    RunEvent, EventType, State,
    RunSubmittedMetadata, PreprocessingMetadata, ErrorOccurredMetadata,
    StateTransitionMetadata, EngineStatusUpdateMetadata, RunSubmittedToEngineMetadata,
    ExtendedRunEvents, SampleId
)


class TestRunEventDeserialization:
    """Test suite for RunEvent model deserialization with discriminated unions."""

    @pytest.fixture
    def base_run_event_data(self) -> Dict[str, Any]:
        """Base run event data structure."""
        return {
            "id": str(uuid.uuid4()),
            "created_at": "2023-11-20T10:00:00Z",
        }

    @pytest.fixture
    def sample_run_submitted_data(self, base_run_event_data) -> Dict[str, Any]:
        """Sample RUN_SUBMITTED event data."""
        return {
            **base_run_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED",
                "message": "Run submitted successfully",
                "start_time": "2023-11-20T10:00:00Z",
                "submitted_by": "user@example.com",
                "state": "QUEUED",
                "workflow_id": "workflow-123",
                "workflow_version_id": "version-456",
                "workflow_url": "https://dockstore.org/api/ga4gh/trs/v2/tools/github.com%2Fuser%2Frepo/versions/main",
                "workflow_name": "example-workflow",
                "workflow_version": "v1.0.0",
                "workflow_authors": ["Author One", "Author Two"],
                "workflow_type": "WDL",
                "workflow_type_version": "1.0",
                "tags": {
                    "project": "test-project",
                    "environment": "dev"
                },
                "sample_ids": [
                    {
                        "id": "sample-1",
                        "storage_account_id": "storage-123"
                    },
                    {
                        "id": "sample-2",
                        "storage_account_id": "storage-456"
                    }
                ]
            }
        }

    @pytest.fixture
    def sample_preprocessing_data(self, base_run_event_data) -> Dict[str, Any]:
        """Sample PREPROCESSING event data."""
        return {
            **base_run_event_data,
            "event_type": "PREPROCESSING",
            "metadata": {
                "event_type": "PREPROCESSING",
                "message": "Preprocessing workflow parameters",
                "outcome": "SUCCESS"
            }
        }

    @pytest.fixture
    def sample_error_occurred_data(self, base_run_event_data) -> Dict[str, Any]:
        """Sample ERROR_OCCURRED event data."""
        return {
            **base_run_event_data,
            "event_type": "ERROR_OCCURRED",
            "metadata": {
                "event_type": "ERROR_OCCURRED",
                "message": "Workflow execution failed",
                "errors": [
                    "Task 'process_sample' failed with exit code 1",
                    "Input file not found: /data/input.txt"
                ]
            }
        }

    @pytest.fixture
    def sample_state_transition_data(self, base_run_event_data) -> Dict[str, Any]:
        """Sample STATE_TRANSITION event data."""
        return {
            **base_run_event_data,
            "event_type": "STATE_TRANSITION",
            "metadata": {
                "event_type": "STATE_TRANSITION",
                "message": "Workflow state changed",
                "end_time": "2023-11-20T10:30:00Z",
                "old_state": "RUNNING",
                "new_state": "COMPLETE",
                "errors": []
            }
        }

    @pytest.fixture
    def sample_engine_status_update_data(self, base_run_event_data) -> Dict[str, Any]:
        """Sample ENGINE_STATUS_UPDATE event data."""
        return {
            **base_run_event_data,
            "event_type": "ENGINE_STATUS_UPDATE",
            "metadata": {
                "event_type": "ENGINE_STATUS_UPDATE",
                "message": "Engine status updated"
            }
        }

    @pytest.fixture
    def sample_run_submitted_to_engine_data(self, base_run_event_data) -> Dict[str, Any]:
        """Sample RUN_SUBMITTED_TO_ENGINE event data."""
        return {
            **base_run_event_data,
            "event_type": "RUN_SUBMITTED_TO_ENGINE",
            "metadata": {
                "event_type": "RUN_SUBMITTED_TO_ENGINE",
                "message": "Run submitted to execution engine"
            }
        }

    def test_run_submitted_event_deserialization(self, sample_run_submitted_data):
        """Test deserialization of RUN_SUBMITTED event."""
        event = RunEvent(**sample_run_submitted_data)
        
        assert event.event_type == EventType.RUN_SUBMITTED
        assert isinstance(event.metadata, RunSubmittedMetadata)
        assert event.metadata.event_type == EventType.RUN_SUBMITTED
        assert event.metadata.message == "Run submitted successfully"
        assert event.metadata.submitted_by == "user@example.com"
        assert event.metadata.state == State.QUEUED
        assert event.metadata.workflow_name == "example-workflow"
        assert event.metadata.workflow_authors == ["Author One", "Author Two"]
        assert event.metadata.tags == {"project": "test-project", "environment": "dev"}
        assert len(event.metadata.sample_ids) == 2
        assert event.metadata.sample_ids[0].id == "sample-1"
        assert event.metadata.sample_ids[0].storage_account_id == "storage-123"

    def test_preprocessing_event_deserialization(self, sample_preprocessing_data):
        """Test deserialization of PREPROCESSING event."""
        event = RunEvent(**sample_preprocessing_data)
        
        assert event.event_type == EventType.PREPROCESSING
        assert isinstance(event.metadata, PreprocessingMetadata)
        assert event.metadata.event_type == EventType.PREPROCESSING
        assert event.metadata.outcome == "SUCCESS"

    def test_error_occurred_event_deserialization(self, sample_error_occurred_data):
        """Test deserialization of ERROR_OCCURRED event."""
        event = RunEvent(**sample_error_occurred_data)
        
        assert event.event_type == EventType.ERROR_OCCURRED
        assert isinstance(event.metadata, ErrorOccurredMetadata)
        assert event.metadata.event_type == EventType.ERROR_OCCURRED
        assert len(event.metadata.errors) == 2
        assert "Task 'process_sample' failed" in event.metadata.errors[0]

    def test_state_transition_event_deserialization(self, sample_state_transition_data):
        """Test deserialization of STATE_TRANSITION event."""
        event = RunEvent(**sample_state_transition_data)
        
        assert event.event_type == EventType.STATE_TRANSITION
        assert isinstance(event.metadata, StateTransitionMetadata)
        assert event.metadata.event_type == EventType.STATE_TRANSITION
        assert event.metadata.old_state == State.RUNNING
        assert event.metadata.new_state == State.COMPLETE
        assert event.metadata.errors == []

    def test_engine_status_update_event_deserialization(self, sample_engine_status_update_data):
        """Test deserialization of ENGINE_STATUS_UPDATE event."""
        event = RunEvent(**sample_engine_status_update_data)
        
        assert event.event_type == EventType.ENGINE_STATUS_UPDATE
        assert isinstance(event.metadata, EngineStatusUpdateMetadata)
        assert event.metadata.event_type == EventType.ENGINE_STATUS_UPDATE

    def test_run_submitted_to_engine_event_deserialization(self, sample_run_submitted_to_engine_data):
        """Test deserialization of RUN_SUBMITTED_TO_ENGINE event."""
        event = RunEvent(**sample_run_submitted_to_engine_data)
        
        assert event.event_type == EventType.RUN_SUBMITTED_TO_ENGINE
        assert isinstance(event.metadata, RunSubmittedToEngineMetadata)
        assert event.metadata.event_type == EventType.RUN_SUBMITTED_TO_ENGINE

    def test_extended_run_events_deserialization(self, sample_run_submitted_data, sample_error_occurred_data):
        """Test deserialization of ExtendedRunEvents containing multiple events."""
        events_data = {
            "events": [
                sample_run_submitted_data,
                sample_error_occurred_data
            ]
        }
        
        extended_run_events = ExtendedRunEvents(**events_data)
        
        assert len(extended_run_events.events) == 2
        assert extended_run_events.events[0].event_type == EventType.RUN_SUBMITTED
        assert extended_run_events.events[1].event_type == EventType.ERROR_OCCURRED

    def test_invalid_event_type_raises_validation_error(self, base_run_event_data):
        """Test that invalid event type raises ValidationError."""
        invalid_data = {
            **base_run_event_data,
            "event_type": "INVALID_EVENT_TYPE",
            "metadata": {
                "event_type": "INVALID_EVENT_TYPE",
                "message": "This should fail"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RunEvent(**invalid_data)
        
        assert "event_type" in str(exc_info.value)


    def test_missing_metadata_raises_validation_error(self, base_run_event_data):
        """Test that missing metadata field raises ValidationError."""
        invalid_data = {
            **base_run_event_data,
            "event_type": "RUN_SUBMITTED"
            # Missing metadata field
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RunEvent(**invalid_data)
        
        assert "metadata" in str(exc_info.value)

    def test_optional_fields_can_be_none(self, base_run_event_data):
        """Test that optional fields can be None without raising errors."""
        minimal_data = {
            **base_run_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED",
                # All other fields are optional and should default to None
            }
        }
        
        event = RunEvent(**minimal_data)
        assert event.metadata.message is None
        assert event.metadata.submitted_by is None
        assert event.metadata.workflow_authors is None
        assert event.metadata.tags is None
        assert event.metadata.sample_ids is None

    def test_sample_id_deserialization(self):
        """Test SampleId model deserialization."""
        sample_data = {
            "id": "sample-123",
            "storage_account_id": "storage-456"
        }
        
        sample_id = SampleId(**sample_data)
        assert sample_id.id == "sample-123"
        assert sample_id.storage_account_id == "storage-456"

    def test_sample_id_optional_fields(self):
        """Test SampleId with optional fields."""
        minimal_sample_data = {}
        
        sample_id = SampleId(**minimal_sample_data)
        assert sample_id.id is None
        assert sample_id.storage_account_id is None

    def test_datetime_parsing(self, base_run_event_data):
        """Test that datetime strings are properly parsed."""
        data_with_datetime = {
            **base_run_event_data,
            "created_at": "2023-11-20T10:00:00.123456Z",
            "event_type": "PREPROCESSING",
            "metadata": {
                "event_type": "PREPROCESSING",
                "outcome": "SUCCESS"
            }
        }
        
        event = RunEvent(**data_with_datetime)
        assert isinstance(event.created_at, datetime)
        assert event.created_at.year == 2023
        assert event.created_at.month == 11
        assert event.created_at.day == 20

    def test_state_enum_validation(self, base_run_event_data):
        """Test that State enum values are properly validated."""
        valid_states = ["QUEUED", "RUNNING", "COMPLETE", "CANCELED", "EXECUTOR_ERROR"]
        
        for state in valid_states:
            data = {
                **base_run_event_data,
                "event_type": "STATE_TRANSITION",
                "metadata": {
                    "event_type": "STATE_TRANSITION",
                    "old_state": "QUEUED",
                    "new_state": state
                }
            }
            
            event = RunEvent(**data)
            assert event.metadata.new_state.value == state

    def test_invalid_state_raises_validation_error(self, base_run_event_data):
        """Test that invalid State values raise ValidationError."""
        invalid_data = {
            **base_run_event_data,
            "event_type": "STATE_TRANSITION",
            "metadata": {
                "event_type": "STATE_TRANSITION",
                "old_state": "INVALID_STATE",
                "new_state": "COMPLETE"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RunEvent(**invalid_data)
        
        assert "old_state" in str(exc_info.value)

    @pytest.mark.parametrize("event_type,metadata_class", [
        (EventType.RUN_SUBMITTED, RunSubmittedMetadata),
        (EventType.PREPROCESSING, PreprocessingMetadata),
        (EventType.ERROR_OCCURRED, ErrorOccurredMetadata),
        (EventType.STATE_TRANSITION, StateTransitionMetadata),
        (EventType.ENGINE_STATUS_UPDATE, EngineStatusUpdateMetadata),
        (EventType.RUN_SUBMITTED_TO_ENGINE, RunSubmittedToEngineMetadata),
    ])
    def test_discriminator_mapping(self, base_run_event_data, event_type, metadata_class):
        """Test that discriminator correctly maps event types to metadata classes."""
        data = {
            **base_run_event_data,
            "event_type": event_type.value,
            "metadata": {
                "event_type": event_type.value,
                "message": f"Test {event_type.value} event"
            }
        }
        
        event = RunEvent(**data)
        assert isinstance(event.metadata, metadata_class)
        assert event.metadata.event_type == event_type

    def test_json_serialization_roundtrip(self, sample_run_submitted_data):
        """Test that RunEvent can be serialized to JSON and deserialized back."""
        # First deserialization
        event = RunEvent(**sample_run_submitted_data)
        
        # Serialize to JSON
        json_str = event.model_dump_json()
        json_dict = json.loads(json_str)
        
        # Deserialize from JSON
        event_from_json = RunEvent(**json_dict)
        
        # Verify they're equivalent
        assert event.id == event_from_json.id
        assert event.event_type == event_from_json.event_type
        assert event.created_at == event_from_json.created_at
        assert type(event.metadata) is type(event_from_json.metadata)
        assert event.metadata.message == event_from_json.metadata.message

    def test_dict_serialization_roundtrip(self, sample_error_occurred_data):
        """Test that RunEvent can be converted to dict and back."""
        # First deserialization
        event = RunEvent(**sample_error_occurred_data)
        
        # Convert to dict
        event_dict = event.model_dump()
        
        # Create new instance from dict
        event_from_dict = RunEvent(**event_dict)
        
        # Verify they're equivalent
        assert event.id == event_from_dict.id
        assert event.event_type == event_from_dict.event_type
        assert event.metadata.errors == event_from_dict.metadata.errors

    def test_empty_events_list(self):
        """Test ExtendedRunEvents with empty events list."""
        data = {"events": []}
        
        extended_run_events = ExtendedRunEvents(**data)
        assert extended_run_events.events == []

    def test_none_events_list(self):
        """Test ExtendedRunEvents with None events list."""
        data = {"events": None}
        
        extended_run_events = ExtendedRunEvents(**data)
        assert extended_run_events.events is None

    def test_no_events_field(self):
        """Test ExtendedRunEvents with no events field."""
        data = {}
        
        extended_run_events = ExtendedRunEvents(**data)
        assert extended_run_events.events is None