import platform
import secrets
from typing import Literal

from dnastack.common.environments import env
from dnastack.common.logger import get_logger

logger = get_logger(__name__)

try:
    import importlib.metadata
    _DNASTACK_VERSION = importlib.metadata.version('dnastack-client-library')
except Exception:
    _DNASTACK_VERSION = 'unknown'


def build_otlp_span(
    question_name: str,
    collection: str,
    start_time_ns: int,
    end_time_ns: int,
    outcome: Literal['success', 'error'],
    row_count: int | None = None,
) -> dict:
    """Build an OTLP-compliant JSON trace payload for a single question execution span."""
    trace_id = env('DNASTACK_TRACE_ID', description='Override trace ID for grouping spans across a pipeline run') or secrets.token_hex(16)
    span_id = secrets.token_hex(8)
    status_code = 1 if outcome == 'success' else 2  # OTLP: OK=1, ERROR=2

    return {
        "resourceSpans": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "dnastack-client"}},
                    {"key": "service.version", "value": {"stringValue": _DNASTACK_VERSION}},
                ]
            },
            "scopeSpans": [{
                "scope": {"name": "dnastack.publisher.questions"},
                "spans": [{
                    "traceId": trace_id,
                    "spanId": span_id,
                    "name": "publisher.question.execute",
                    "startTimeUnixNano": str(start_time_ns),
                    "endTimeUnixNano": str(end_time_ns),
                    "status": {"code": status_code},
                    "attributes": [
                        {"key": "question.name", "value": {"stringValue": question_name}},
                        {"key": "question.collection", "value": {"stringValue": collection}},
                        {"key": "question.outcome", "value": {"stringValue": outcome}},
                        {"key": "question.duration_ms", "value": {"doubleValue": (end_time_ns - start_time_ns) / 1_000_000}},
                        *([{"key": "question.row_count", "value": {"intValue": row_count}}] if row_count is not None else []),
                        {"key": "runtime.python", "value": {"stringValue": platform.python_version()}},
                    ],
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
        payload = build_otlp_span(question_name, collection, start_time_ns, end_time_ns, outcome, row_count)
        client.submit_telemetry(payload)
    except Exception as e:
        logger.debug(f"Telemetry submission failed (non-fatal): {e}")
