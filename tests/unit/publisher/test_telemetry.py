import time
from unittest.mock import MagicMock

from dnastack.cli.commands.publisher.questions.telemetry import build_otlp_log, submit_telemetry


class TestBuildOtlpLog:

    def test_returns_valid_otlp_logs_structure(self):
        start_ns = time.time_ns()
        end_ns = start_ns + 1_000_000_000
        payload = build_otlp_log('my-question', 'my-collection', start_ns, end_ns, 'success')

        assert 'resourceLogs' in payload
        resource_logs = payload['resourceLogs']
        assert len(resource_logs) == 1
        scope_logs = resource_logs[0]['scopeLogs']
        assert len(scope_logs) == 1
        log_records = scope_logs[0]['logRecords']
        assert len(log_records) == 1

    def test_success_outcome_sets_severity_info(self):
        lr = _first_log_record(build_otlp_log('q', 'c', 0, 1, 'success'))
        assert lr['severityNumber'] == 9

    def test_error_outcome_sets_severity_error(self):
        lr = _first_log_record(build_otlp_log('q', 'c', 0, 1, 'error'))
        assert lr['severityNumber'] == 17

    def test_attributes_include_question_name_and_collection(self):
        lr = _first_log_record(build_otlp_log('my-q', 'my-col', 0, 1, 'success'))
        attrs = _string_attrs(lr)
        assert attrs['question.name'] == 'my-q'
        assert attrs['question.collection'] == 'my-col'
        assert attrs['question.outcome'] == 'success'

    def test_duration_ms_is_calculated_from_start_and_end(self):
        start_ns = 1_000_000_000
        end_ns = 2_500_000_000  # 1500 ms later
        lr = _first_log_record(build_otlp_log('q', 'c', start_ns, end_ns, 'success'))
        double_attrs = _double_attrs(lr)
        assert double_attrs['question.duration_ms'] == 1500.0

    def test_row_count_included_when_provided(self):
        lr = _first_log_record(build_otlp_log('q', 'c', 0, 1, 'success', row_count=42))
        assert _double_attrs(lr)['question.row_count'] == 42.0

    def test_row_count_omitted_when_not_provided(self):
        lr = _first_log_record(build_otlp_log('q', 'c', 0, 1, 'error'))
        assert 'question.row_count' not in [a['key'] for a in lr['attributes']]

    def test_resource_attributes_include_service_name(self):
        payload = build_otlp_log('q', 'c', 0, 1, 'success')
        resource_attrs = {a['key']: a['value']['stringValue']
                         for a in payload['resourceLogs'][0]['resource']['attributes']}
        assert resource_attrs['service.name'] == 'dnastack-client'

    def test_time_unix_nano_is_end_time(self):
        end_ns = 1_713_369_601_000_000_000
        lr = _first_log_record(build_otlp_log('q', 'c', 0, end_ns, 'success'))
        assert lr['timeUnixNano'] == str(end_ns)

    def test_success_message_includes_question_name_and_duration(self):
        start_ns = 0
        end_ns = 1_500_000_000  # 1500 ms
        lr = _first_log_record(build_otlp_log('my-question', 'c', start_ns, end_ns, 'success'))
        assert 'my-question' in lr['body']['stringValue']
        assert '1500.0ms' in lr['body']['stringValue']

    def test_success_message_includes_row_count_when_provided(self):
        lr = _first_log_record(build_otlp_log('q', 'c', 0, 1_000_000_000, 'success', row_count=7))
        assert '7 rows' in lr['body']['stringValue']

    def test_error_message_includes_question_name_and_duration(self):
        lr = _first_log_record(build_otlp_log('bad-question', 'c', 0, 500_000_000, 'error'))
        assert 'bad-question' in lr['body']['stringValue']
        assert '500.0ms' in lr['body']['stringValue']


class TestSubmitTelemetry:

    def test_calls_client_submit_telemetry(self):
        client = MagicMock()
        submit_telemetry(client, 'q', 'c', 0, 1, 'success')
        client.submit_telemetry.assert_called_once()

    def test_swallows_client_errors_silently(self):
        client = MagicMock()
        client.submit_telemetry.side_effect = Exception("network error")
        submit_telemetry(client, 'q', 'c', 0, 1, 'success')  # must not raise


def _first_log_record(otlp_payload: dict) -> dict:
    return otlp_payload['resourceLogs'][0]['scopeLogs'][0]['logRecords'][0]


def _string_attrs(log_record: dict) -> dict:
    return {a['key']: a['value']['stringValue'] for a in log_record['attributes'] if 'stringValue' in a['value']}


def _double_attrs(log_record: dict) -> dict:
    return {a['key']: a['value']['doubleValue'] for a in log_record['attributes'] if 'doubleValue' in a['value']}
