import platform
from typing import Literal

from dnastack.common.logger import get_logger

logger = get_logger(__name__)

try:
    import importlib.metadata
    _DNASTACK_VERSION = importlib.metadata.version('dnastack-client-library')
except Exception:
    _DNASTACK_VERSION = 'unknown'

_SEVERITY_INFO = 9
_SEVERITY_ERROR = 17


def _build_message(question_name: str, outcome: Literal['success', 'error'], duration_ms: float, row_count: int | None) -> str:
    if outcome == 'success':
        suffix = f" ({row_count} rows)" if row_count is not None else ""
        return f"Question '{question_name}' executed successfully in {duration_ms:.1f}ms{suffix}"
    else:
        return f"Question '{question_name}' failed after {duration_ms:.1f}ms"


def build_otlp_log(
    question_name: str,
    collection: str,
    start_time_ns: int,
    end_time_ns: int,
    outcome: Literal['success', 'error'],
    row_count: int | None = None,
) -> dict:
    """Build an OTLP logs JSON payload for a single question execution event."""
    duration_ms = (end_time_ns - start_time_ns) / 1_000_000
    severity = _SEVERITY_INFO if outcome == 'success' else _SEVERITY_ERROR
    message = _build_message(question_name, outcome, duration_ms, row_count)

    attributes = [
        {"key": "question.name", "value": {"stringValue": question_name}},
        {"key": "question.collection", "value": {"stringValue": collection}},
        {"key": "question.outcome", "value": {"stringValue": outcome}},
        {"key": "question.duration_ms", "value": {"doubleValue": duration_ms}},
        *([{"key": "question.row_count", "value": {"doubleValue": float(row_count)}}] if row_count is not None else []),
        {"key": "runtime.python", "value": {"stringValue": platform.python_version()}},
    ]

    return {
        "resourceLogs": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "dnastack-client"}},
                    {"key": "service.version", "value": {"stringValue": _DNASTACK_VERSION}},
                ]
            },
            "scopeLogs": [{
                "scope": {"name": "dnastack.publisher.questions"},
                "logRecords": [{
                    "timeUnixNano": str(end_time_ns),
                    "severityNumber": severity,
                    "body": {"stringValue": message},
                    "attributes": attributes,
                }]
            }]
        }]
    }


def submit_telemetry(
    client,
    question_name: str,
    collection: str,
    start_time_ns: int,
    end_time_ns: int,
    outcome: Literal['success', 'error'],
    row_count: int | None = None,
) -> None:
    """Submit OTLP telemetry to collection-service. Errors are silently swallowed."""
    try:
        payload = build_otlp_log(question_name, collection, start_time_ns, end_time_ns, outcome, row_count)
        client.submit_telemetry(payload)
    except Exception as e:
        logger.debug(f"Telemetry submission failed (non-fatal): {e}")
