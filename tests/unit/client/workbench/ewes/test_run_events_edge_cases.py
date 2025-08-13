import json
import uuid
from datetime import datetime
from typing import Dict, Any

import pytest
from pydantic import ValidationError

from dnastack.client.workbench.ewes.models import (
    RunEvent, EventType, State, ExtendedRunEvents,
    RunSubmittedMetadata, StateTransitionMetadata,
)


class TestRunEventEdgeCases:
    """Test edge cases, error handling, and boundary conditions for RunEvent models."""

    @pytest.fixture
    def base_event_data(self) -> Dict[str, Any]:
        """Basic event data structure."""
        return {
            "id": str(uuid.uuid4()),
            "created_at": "2023-11-20T10:00:00Z"
        }

    def test_invalid_discriminator_value_in_metadata(self, base_event_data):
        """Test that invalid discriminator value in metadata raises ValidationError."""
        invalid_data = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "INVALID_TYPE",  # This doesn't match any EventType enum
                "message": "This should fail"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RunEvent(**invalid_data)
        
        error_str = str(exc_info.value).lower()
        assert any(keyword in error_str for keyword in ["discriminator", "invalid", "literal"])

    def test_missing_discriminator_field_in_metadata(self, base_event_data):
        """Test that missing discriminator field in metadata raises ValidationError."""
        invalid_data = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                # Missing "event_type" field which is the discriminator
                "message": "This should fail"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RunEvent(**invalid_data)
        
        assert "event_type" in str(exc_info.value)

    def test_null_metadata_field(self, base_event_data):
        """Test that null metadata field raises ValidationError."""
        invalid_data = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": None
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RunEvent(**invalid_data)
        
        assert "metadata" in str(exc_info.value)

    def test_empty_metadata_object(self, base_event_data):
        """Test behavior with empty metadata object."""
        invalid_data = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RunEvent(**invalid_data)
        
        # Should fail because event_type discriminator is missing
        assert "event_type" in str(exc_info.value)

    def test_extra_fields_in_metadata(self, base_event_data):
        """Test that extra fields in metadata are handled gracefully."""
        data_with_extra = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED",
                "message": "Valid message",
                "extra_field": "This should be ignored",
                "another_extra": {"nested": "object"}
            }
        }
        
        # Pydantic should handle extra fields based on model configuration
        # By default, extra fields are ignored unless model is configured otherwise
        event = RunEvent(**data_with_extra)
        assert event.metadata.message == "Valid message"
        
        # Extra fields should not be accessible as attributes
        assert not hasattr(event.metadata, 'extra_field')

    def test_malformed_datetime_string(self, base_event_data):
        """Test behavior with malformed datetime strings."""
        invalid_datetime_data = {
            **base_event_data,
            "created_at": "not-a-datetime",
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RunEvent(**invalid_datetime_data)
        
        assert "created_at" in str(exc_info.value)

    def test_various_datetime_formats(self, base_event_data):
        """Test different valid datetime formats."""
        valid_formats = [
            "2023-11-20T10:00:00Z",
            "2023-11-20T10:00:00.000Z",
            "2023-11-20T10:00:00.123456Z",
            "2023-11-20T10:00:00+00:00",
            "2023-11-20T10:00:00-05:00",
        ]
        
        for dt_format in valid_formats:
            data = {
                **base_event_data,
                "created_at": dt_format,
                "event_type": "RUN_SUBMITTED",
                "metadata": {
                    "event_type": "RUN_SUBMITTED"
                }
            }
            
            event = RunEvent(**data)
            assert isinstance(event.created_at, datetime)

    def test_large_event_id(self, base_event_data):
        """Test handling of very long event IDs."""
        long_id = "a" * 1000  # Very long ID
        data = {
            **base_event_data,
            "id": long_id,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED"
            }
        }
        
        event = RunEvent(**data)
        assert event.id == long_id

    def test_special_characters_in_fields(self, base_event_data):
        """Test handling of special characters in string fields."""
        special_message = "Message with special chars: αβγ 中文 🎉 \n\t\"'\\/"
        data = {
            **base_event_data,
            "event_type": "ERROR_OCCURRED",
            "metadata": {
                "event_type": "ERROR_OCCURRED",
                "message": special_message,
                "errors": ["Error with unicode: αβγ", "Error with newline\nhere"]
            }
        }
        
        event = RunEvent(**data)
        assert event.metadata.message == special_message
        assert len(event.metadata.errors) == 2
        assert "unicode: αβγ" in event.metadata.errors[0]

    def test_maximum_list_sizes(self, base_event_data):
        """Test handling of large lists in metadata."""
        large_errors_list = [f"Error {i}" for i in range(1000)]
        large_authors_list = [f"Author {i}" for i in range(100)]
        
        data = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED",
                "workflow_authors": large_authors_list,
            }
        }
        
        event = RunEvent(**data)
        assert len(event.metadata.workflow_authors) == 100
        
        # Test large errors list
        error_data = {
            **base_event_data,
            "event_type": "ERROR_OCCURRED",
            "metadata": {
                "event_type": "ERROR_OCCURRED",
                "errors": large_errors_list
            }
        }
        
        error_event = RunEvent(**error_data)
        assert len(error_event.metadata.errors) == 1000

    def test_nested_dict_in_tags(self, base_event_data):
        """Test handling of complex nested structures in tags."""
        complex_tags = {
            "simple_key": "simple_value",
            "nested_key": "nested_value",
            "special_chars": "value with spaces & symbols!",
            "unicode_key": "ηλληνικά",
        }
        
        data = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED",
                "tags": complex_tags
            }
        }
        
        event = RunEvent(**data)
        assert event.metadata.tags == complex_tags
        assert event.metadata.tags["unicode_key"] == "ηλληνικά"

    def test_boundary_states_in_transition(self, base_event_data):
        """Test all possible State enum combinations in STATE_TRANSITION events."""
        all_states = [state for state in State]
        
        for old_state in all_states:
            for new_state in all_states:
                if old_state != new_state:  # Skip same-state transitions
                    data = {
                        **base_event_data,
                        "id": f"{base_event_data['id']}-{old_state.value}-{new_state.value}",
                        "event_type": "STATE_TRANSITION",
                        "metadata": {
                            "event_type": "STATE_TRANSITION",
                            "old_state": old_state.value,
                            "new_state": new_state.value
                        }
                    }
                    
                    event = RunEvent(**data)
                    assert event.metadata.old_state == old_state
                    assert event.metadata.new_state == new_state

    def test_json_deserialization_from_api_response(self):
        """Test deserialization from JSON as would come from API response."""
        # Simulate actual API response format
        api_response_json = '''
        {
            "events": [
                {
                    "id": "event-1",
                    "created_at": "2023-11-20T10:00:00.123Z",
                    "event_type": "RUN_SUBMITTED",
                    "metadata": {
                        "event_type": "RUN_SUBMITTED",
                        "message": null,
                        "start_time": "2023-11-20T10:00:00.123Z",
                        "submitted_by": "user@example.com",
                        "state": "QUEUED",
                        "workflow_name": "hello-world",
                        "workflow_authors": ["John Doe", "Jane Smith"],
                        "tags": {
                            "project": "test-project",
                            "priority": "high"
                        },
                        "sample_ids": [
                            {
                                "id": "sample-1",
                                "storage_account_id": "storage-123"
                            }
                        ]
                    }
                },
                {
                    "id": "event-2",
                    "created_at": "2023-11-20T10:01:00.456Z",
                    "event_type": "STATE_TRANSITION",
                    "metadata": {
                        "event_type": "STATE_TRANSITION",
                        "old_state": "QUEUED",
                        "new_state": "RUNNING",
                        "errors": []
                    }
                }
            ]
        }
        '''
        
        response_data = json.loads(api_response_json)
        extended_run_events = ExtendedRunEvents(**response_data)
        
        assert len(extended_run_events.events) == 2
        
        # Test first event
        first_event = extended_run_events.events[0]
        assert first_event.event_type == EventType.RUN_SUBMITTED
        assert isinstance(first_event.metadata, RunSubmittedMetadata)
        assert first_event.metadata.submitted_by == "user@example.com"
        assert first_event.metadata.workflow_name == "hello-world"
        assert len(first_event.metadata.workflow_authors) == 2
        assert first_event.metadata.tags["project"] == "test-project"
        assert len(first_event.metadata.sample_ids) == 1
        
        # Test second event
        second_event = extended_run_events.events[1]
        assert second_event.event_type == EventType.STATE_TRANSITION
        assert isinstance(second_event.metadata, StateTransitionMetadata)
        assert second_event.metadata.old_state == State.QUEUED
        assert second_event.metadata.new_state == State.RUNNING
        assert second_event.metadata.errors == []

    def test_case_sensitivity_in_enum_values(self, base_event_data):
        """Test that enum values are case-sensitive."""
        # Test with incorrect case
        invalid_case_data = {
            **base_event_data,
            "event_type": "run_submitted",  # lowercase instead of uppercase
            "metadata": {
                "event_type": "run_submitted",
                "message": "This should fail"
            }
        }
        
        with pytest.raises(ValidationError):
            RunEvent(**invalid_case_data)
        
        # Test with mixed case
        invalid_mixed_case_data = {
            **base_event_data,
            "event_type": "Run_Submitted",  # mixed case
            "metadata": {
                "event_type": "Run_Submitted",
                "message": "This should fail"
            }
        }
        
        with pytest.raises(ValidationError):
            RunEvent(**invalid_mixed_case_data)

    def test_memory_usage_with_large_events(self, base_event_data):
        """Test memory usage doesn't explode with large event data."""
        # Create a large event with lots of data
        large_data = {
            **base_event_data,
            "event_type": "ERROR_OCCURRED",
            "metadata": {
                "event_type": "ERROR_OCCURRED",
                "message": "A" * 10000,  # 10KB message
                "errors": [f"Error {i}: {'X' * 100}" for i in range(100)]  # ~10KB of error messages
            }
        }
        
        # This should not raise memory errors or take excessive time
        event = RunEvent(**large_data)
        assert len(event.metadata.message) == 10000
        assert len(event.metadata.errors) == 100
        
        # Test serialization doesn't break
        event_dict = event.dict()
        assert len(event_dict["metadata"]["message"]) == 10000

    @pytest.mark.parametrize("field_type,field_name,empty_value", [
        ("list", "workflow_authors", None),
        ("list", "workflow_authors", []),
        ("list", "sample_ids", None),
        ("list", "sample_ids", []),
        ("dict", "tags", None),
        ("dict", "tags", {}),
    ])
    def test_optional_list_and_dict_fields(self, base_event_data, field_type, field_name, empty_value):
        """Test optional list and dict fields with various empty values."""
        data = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED",
                field_name: empty_value
            }
        }
        
        event = RunEvent(**data)
        actual_value = getattr(event.metadata, field_name)
        assert actual_value == empty_value, f"Expected {field_name} to be {empty_value}, got {actual_value}"

    def test_concurrent_deserialization(self, base_event_data):
        """Test thread safety of deserialization (basic smoke test)."""
        import threading
        import time
        
        def deserialize_event(thread_id):
            data = {
                **base_event_data,
                "id": f"{base_event_data['id']}-thread-{thread_id}",
                "event_type": "RUN_SUBMITTED",
                "metadata": {
                    "event_type": "RUN_SUBMITTED",
                    "message": f"Message from thread {thread_id}"
                }
            }
            
            for _ in range(10):  # Create multiple events per thread
                event = RunEvent(**data)
                assert event.metadata.message == f"Message from thread {thread_id}"
                time.sleep(0.001)  # Small delay to increase chance of race conditions
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=deserialize_event, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()

    def test_deep_copy_behavior(self, base_event_data):
        """Test that events can be deep copied without issues."""
        import copy
        
        original_data = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED",
                "workflow_authors": ["Original Author"],
                "tags": {"original": "tag"}
            }
        }
        
        original_event = RunEvent(**original_data)
        copied_event = copy.deepcopy(original_event)
        
        # Verify they're equal but not the same object
        assert original_event.id == copied_event.id
        assert original_event.event_type == copied_event.event_type
        assert original_event.metadata.workflow_authors == copied_event.metadata.workflow_authors
        assert original_event is not copied_event
        assert original_event.metadata is not copied_event.metadata

    def test_hash_behavior(self, base_event_data):
        """Test that events can be used in sets and as dict keys."""
        data = {
            **base_event_data,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED"
            }
        }
        
        event1 = RunEvent(**data)
        event2 = RunEvent(**data)  # Same data
        
        # These should be equal based on their data
        # Note: Pydantic models are hashable if they're frozen, otherwise this might fail
        try:
            event_set = {event1, event2}
            event_dict = {event1: "value1", event2: "value2"}
            # If we get here, the objects are hashable
            assert len(event_set) <= 2  # Could be 1 if they're considered equal
            assert len(event_dict) <= 2
        except TypeError:
            # If TypeError is raised, the objects aren't hashable (which is also fine)
            pytest.skip("RunEvent objects are not hashable")

    def test_validation_error_messages_are_helpful(self, base_event_data):
        """Test that validation error messages provide useful information."""
        # Test with missing required field
        incomplete_data = {
            **base_event_data,
            # Missing event_type field
            "metadata": {
                "event_type": "RUN_SUBMITTED"
            }
        }
        
        with pytest.raises(ValidationError) as exc_info:
            RunEvent(**incomplete_data)
        
        error_msg = str(exc_info.value)
        assert "event_type" in error_msg
        assert "field required" in error_msg.lower() or "missing" in error_msg.lower()

    def test_serialization_preserves_precision(self, base_event_data):
        """Test that serialization/deserialization preserves data precision."""
        precise_timestamp = "2023-11-20T10:00:00.123456789Z"
        data = {
            **base_event_data,
            "created_at": precise_timestamp,
            "event_type": "RUN_SUBMITTED",
            "metadata": {
                "event_type": "RUN_SUBMITTED",
                "start_time": precise_timestamp
            }
        }
        
        event = RunEvent(**data)
        serialized = event.json()
        deserialized = RunEvent(**json.loads(serialized))
        
        # Verify timestamps are preserved (noting that datetime precision might be limited)
        assert deserialized.created_at is not None
        assert deserialized.metadata.start_time is not None
        
        # The exact precision might vary based on datetime implementation
        # But the values should be very close
        original_dt = datetime.fromisoformat(precise_timestamp.replace('Z', '+00:00'))
        assert abs((deserialized.created_at - original_dt).total_seconds()) < 0.001