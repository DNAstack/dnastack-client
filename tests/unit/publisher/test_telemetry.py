import time
from unittest.mock import MagicMock

from dnastack.cli.commands.publisher.questions.telemetry import build_otlp_span, submit_telemetry


class TestBuildOtlpSpan:

    def test_returns_valid_otlp_structure(self):
        start_ns = time.time_ns()
        end_ns = start_ns + 1_000_000_000
        span = build_otlp_span('my-question', 'my-collection', start_ns, end_ns, 'success')

        assert 'resourceSpans' in span
        resource_spans = span['resourceSpans']
        assert len(resource_spans) == 1
        scope_spans = resource_spans[0]['scopeSpans']
        assert len(scope_spans) == 1
        spans = scope_spans[0]['spans']
        assert len(spans) == 1
        s = spans[0]
        assert s['name'] == 'publisher.question.execute'
        assert s['startTimeUnixNano'] == str(start_ns)
        assert s['endTimeUnixNano'] == str(end_ns)

    def test_success_outcome_sets_status_code_1(self):
        s = _first_span(build_otlp_span('q', 'c', 0, 1, 'success'))
        assert s['status']['code'] == 1

    def test_error_outcome_sets_status_code_2(self):
        s = _first_span(build_otlp_span('q', 'c', 0, 1, 'error'))
        assert s['status']['code'] == 2

    def test_attributes_include_question_name_and_collection(self):
        s = _first_span(build_otlp_span('my-q', 'my-col', 0, 1, 'success'))
        attrs = {a['key']: a['value']['stringValue'] for a in s['attributes']}
        assert attrs['question.name'] == 'my-q'
        assert attrs['question.collection'] == 'my-col'
        assert attrs['question.outcome'] == 'success'

    def test_resource_attributes_include_service_name(self):
        span = build_otlp_span('q', 'c', 0, 1, 'success')
        resource_attrs = {a['key']: a['value']['stringValue']
                         for a in span['resourceSpans'][0]['resource']['attributes']}
        assert resource_attrs['service.name'] == 'dnastack-client'

    def test_trace_and_span_ids_are_hex_strings(self):
        s = _first_span(build_otlp_span('q', 'c', 0, 1, 'success'))
        assert len(s['traceId']) == 32
        assert len(s['spanId']) == 16
        int(s['traceId'], 16)  # must be valid hex
        int(s['spanId'], 16)


class TestSubmitTelemetry:

    def test_calls_client_submit_telemetry(self):
        client = MagicMock()
        submit_telemetry(client, 'q', 'c', 0, 1, 'success')
        client.submit_telemetry.assert_called_once()

    def test_swallows_client_errors_silently(self):
        client = MagicMock()
        client.submit_telemetry.side_effect = Exception("network error")
        submit_telemetry(client, 'q', 'c', 0, 1, 'success')  # must not raise


def _first_span(otlp_payload: dict) -> dict:
    return otlp_payload['resourceSpans'][0]['scopeSpans'][0]['spans'][0]
