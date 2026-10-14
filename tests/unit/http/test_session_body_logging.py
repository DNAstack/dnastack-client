"""Unit tests for keeping response bodies out of the HttpSession debug log."""
import json
from unittest.mock import Mock, patch

import pytest

from dnastack.client.result_iterator import ResultIterator
from dnastack.client.workbench.base_client import PageableApiError
from dnastack.client.workbench.ewes.client import EngineListResultLoader
from dnastack.client.workbench.ewes.models import ExecutionEngineListOptions
from dnastack.common.logger import TraceableLogger
from dnastack.common.tracing import Span
from dnastack.http.session import HttpSession

MARKER = 'SECRET-IN-BODY'


def _debug_log(log_response_body: bool) -> str:
    requests_session = Mock()
    requests_session.get.return_value = Mock(ok=True, status_code=200, text=f'{{"key": "{MARKER}"}}')
    # Session loggers are standalone TraceableLoggers that caplog cannot see, so record debug() directly.
    with patch.object(TraceableLogger, 'debug', autospec=True) as debug:
        with HttpSession(enable_auth=False, session=requests_session,
                         log_response_body=log_response_body) as session:
            session.get('https://api.example.com/engines/x')
    return '\n'.join(str(call.args[1]) for call in debug.call_args_list if len(call.args) > 1)


def test_response_body_logged_by_default():
    assert MARKER in _debug_log(log_response_body=True)


def test_response_body_not_logged_when_disabled():
    log = _debug_log(log_response_body=False)
    assert MARKER not in log
    assert '(response body not logged)' in log
    assert 'HTTP 200' in log


def _engine_loader_debug_log(log_response_body: bool, body: dict) -> str:
    requests_session = Mock()
    requests_session.get.return_value = Mock(ok=True, status_code=200, text=json.dumps(body),
                                             json=Mock(return_value=body))
    http_session = HttpSession(enable_auth=False, session=requests_session, log_response_body=log_response_body)
    loader = EngineListResultLoader(service_url='https://api.example.com/ns/engines', http_session=http_session,
                                    trace=Span(), list_options=ExecutionEngineListOptions())
    with patch.object(TraceableLogger, 'debug', autospec=True) as debug:
        list(ResultIterator(loader))
    return '\n'.join(str(call.args[1]) for call in debug.call_args_list if len(call.args) > 1)


VALID_BODY = {'engines': [{'id': 'e', 'name': f'{MARKER}', 'provider': 'GCP'}], 'next_page_url': None}


def test_engine_list_loader_does_not_log_body_when_disabled():
    log = _engine_loader_debug_log(False, VALID_BODY)
    assert MARKER not in log
    assert '(response body not logged)' in log


def test_engine_list_loader_logs_body_when_enabled():
    assert MARKER in _engine_loader_debug_log(True, VALID_BODY)


def test_engine_list_loader_errors_do_not_contain_body_when_disabled():
    invalid = {'engines': [{'secret': MARKER}]}
    with pytest.raises(PageableApiError) as invalid_error:
        _engine_loader_debug_log(False, invalid)
    assert MARKER not in str(invalid_error.value)

    requests_session = Mock()
    requests_session.get.return_value = Mock(ok=True, status_code=200, text=MARKER,
                                             json=Mock(side_effect=ValueError(MARKER)))
    http_session = HttpSession(enable_auth=False, session=requests_session, log_response_body=False)
    loader = EngineListResultLoader(service_url='https://api.example.com/ns/engines', http_session=http_session,
                                    trace=Span(), list_options=ExecutionEngineListOptions())
    with pytest.raises(PageableApiError) as non_json_error:
        list(ResultIterator(loader))
    assert MARKER not in str(non_json_error.value)
