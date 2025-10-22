import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from time import time, sleep
from typing import Dict, List, Any, Optional, Union
from unittest import TestCase
from unittest.mock import MagicMock, Mock

from dnastack import ServiceEndpoint
from dnastack.common.tracing import Span
from dnastack.http.authenticators.abstract import Authenticator
from dnastack.http.authenticators.oauth2 import OAuth2Authenticator
from dnastack.http.authenticators.oauth2_adapter.factory import OAuth2AdapterFactory
from dnastack.http.session import HttpSession, ClientError, HttpError
from dnastack.http.session_info import InMemorySessionStorage, SessionManager, SessionInfo
from requests import Session, Response, Request
from pydantic import BaseModel, Field

from tests.util.exam_helper import make_mock_response


class HandledRequest(BaseModel):
    path: str

    # Assume that only one header name can appear once per request.
    headers: Dict[str, str]


class DataCollection(BaseModel):
    handled_requests: List[HandledRequest] = Field(default_factory=list)

    def reset(self):
        self.handled_requests.clear()


class MockWebHandler(BaseHTTPRequestHandler):
    _data_collection = DataCollection()

    @classmethod
    def reset_collected_data(cls):
        """ Reset the collected data. """
        cls._data_collection.reset()

    @classmethod
    def get_collected_data(cls) -> DataCollection:
        """ Provide a copy of the collected data. """
        return cls._data_collection.model_copy(deep=True)

    def _collect_request_data(self):
        """ Collect the information on the incoming request """
        request_url = "localhost:8000" + self.path
        self._data_collection.handled_requests.append(
            HandledRequest(
                path=request_url,
                headers={
                    name: value
                    for name, value in self.headers.items()
                }
            )
        )

    def log_message(self, format, *args):
        # Suppress server log messages during testing
        pass

    def do_GET(self):
        self._collect_request_data()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        response = {'message': 'Test response'}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        self._collect_request_data()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

        # Return token response for any POST request (including /token)
        response = dict(
            access_token='test_access_token',
            refresh_token='test_refresh_token',
            token_type='test_token_type',
            expires_in=60,
        )
        self.wfile.write(json.dumps(response).encode('utf-8'))


class TestHttpSession(TestCase):

    def test_handle_midflight_reauthentication(self):
        mock_session_id = 'foxtrot'
        mock_session_storage = InMemorySessionStorage()
        mock_session_manager = SessionManager(mock_session_storage)
        mock_session_manager.save(mock_session_id, self._make_mock_session_info(ttl=1))

        # ##### Mock the authenticator #####
        # Please note that this mock setup is a bit complicate as we would like the white-box assertion.
        class MockAuthenticator(Authenticator):
            def __init__(self, session_manager: SessionManager, session_id: str):
                super().__init__()
                self._session_manager = session_manager
                self._session_id = session_id

            @property
            def session_id(self):
                return self._session_id

            def authenticate(self, trace_context: Span) -> SessionInfo:
                raise RuntimeError('Unexpected authentication')

            def restore_session(self) -> SessionInfo:
                return self._session_manager.restore(self._session_id)

            def update_request(self, session: SessionInfo, r: Union[Request, Session]) -> Union[Request, Session]:
                pass  # Noop

            def revoke(self):
                self._session_manager.delete(self._session_id)

            def clear_access_token(self):
                session_id = self.session_id

                session_info = self._session_manager.restore(session_id)
                session_info.access_token = None

                self._session_manager.save(session_id, session_info)

            def refresh(self, trace_context: Optional[Span] = None) -> SessionInfo:
                raise RuntimeError('refresh triggered')

        mock_authenticator = MockAuthenticator(mock_session_manager, mock_session_id)

        # ##### Mock response sequence #####
        mock_response_sequence = [
            make_mock_response(401),
            make_mock_response(200),
        ]

        def mock_resource_session_get(*args, **kwargs):
            sleep(1)
            return mock_response_sequence.pop(0)

        mock_resource_session = MagicMock(Session)
        mock_resource_session.get.side_effect = mock_resource_session_get

        # ##### Initiate the test #####
        test_http_session = HttpSession(authenticators=[mock_authenticator], session=mock_resource_session,
                                        suppress_error=False)
        # Expected a "not implemented" error.
        # NOTE: We use this error type as the indicator that the refre
        with self.assertRaisesRegex(RuntimeError, 'refresh triggered'):
            test_http_session.get('https://juliet.november')

    def _make_mock_session_info(self, ttl: int) -> SessionInfo:
        return SessionInfo(access_token='at',
                           refresh_token='rt',
                           issued_at=int(time()),
                           valid_until=int(time() + ttl),
                           token_type='faux')

    def _make_mock_response(self, status_code: int, headers: Optional[Dict] = None, text: Any = None,
                            json: Any = None) -> Response:
        mock_response = MagicMock(Response)
        mock_response.headers = headers or {}
        mock_response.status_code = status_code
        mock_response.ok = 200 <= status_code < 300

        if text:
            mock_response.text = Mock(return_value=text)
            mock_response.json = Mock(return_value=json.loads(text))
        elif json:
            mock_response.text = Mock(return_value=json.dumps(json))
            mock_response.json = Mock(return_value=json)
        else:
            mock_response.text = ''

        return mock_response

    def test_submit_403_status_code(self):
        # Create a mock authenticator
        authenticator_mock = MagicMock(Authenticator)
        authenticator_mock.before_request.return_value = None
        authenticator_mock.session_id = 1

        # Create a mock response with status code 403
        response_mock = Mock()
        response_mock.status_code = 403
        response_mock.ok = False
        response_mock.text = "Test data"

        # Create a mock session
        session_mock = MagicMock(Session)
        session_mock.get.return_value = response_mock

        http_session = HttpSession(authenticators=[authenticator_mock], session=session_mock, suppress_error=False)
        with self.assertRaises(ClientError) as e:
            http_session.submit(method="get", url="http://example-url.com")
        self.assertEqual(e.exception.response.status_code, 403)

    def setUp(self):
        # Start the HTTP server
        MockWebHandler.reset_collected_data()
        self.server = HTTPServer(('localhost', 8000), MockWebHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()

    def tearDown(self):
        # Stop the HTTP server
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()

    def test_tracing_submit_function(self):
        """Test that HTTP session properly handles requests with tracing and OAuth2 authentication"""
        session_storage = InMemorySessionStorage()
        session_manager = SessionManager(session_storage)
        adapter_factory = OAuth2AdapterFactory()
        session = Session()

        auth_info = dict(
            type='oauth2',
            client_id='client_id',
            client_secret='client_secret',
            grant_type='client_credentials',
            resource_url='http://localhost:8000',
            token_endpoint='http://localhost:8000',
        )

        service_endpoint = ServiceEndpoint(
            id='test_endpoint',
            adapter_type='test_adapter',
            url='http://localhost:8000',
            authentication=auth_info,
        )

        url = 'http://localhost:8000/'

        test_authenticator = OAuth2Authenticator(service_endpoint, auth_info, session_manager, adapter_factory)

        http_session = HttpSession(authenticators=[test_authenticator], session=session, suppress_error=False)
        response = http_session.submit("get", url)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json()['message'], 'Test response')

        collected_request_data = MockWebHandler.get_collected_data().handled_requests

        # In this test scenario, we expect to have two requests made where one is for authentication and one for
        # the actual request.
        self.assertEqual(len(collected_request_data), 2)

        first_request_data = collected_request_data[0]

        self.assertIn("X-B3-TraceId", first_request_data.headers.keys())
        self.assertIn("X-B3-SpanId", first_request_data.headers.keys())
        self.assertIsNotNone(first_request_data.path)
        self.assertIn("User-Agent", first_request_data.headers.keys())

        first_header_traceid = first_request_data.headers["X-B3-TraceId"]
        first_header_spanid = first_request_data.headers["X-B3-SpanId"]

        for item in collected_request_data[1:]:
            self.assertEqual(item.headers["X-B3-TraceId"], first_header_traceid)
            self.assertNotEqual(item.headers["X-B3-SpanId"], first_header_spanid)
            self.assertIsNotNone(item.path)
            self.assertIn("User-Agent", item.headers.keys())


class TestHttpErrorAndClientError(TestCase):
    """Test cases for HttpError and ClientError exception classes"""

    def setUp(self):
        self.mock_response = Mock(spec=Response)
        self.mock_response.status_code = 404
        self.mock_response.text = "Not Found"
        
        # Create a mock trace
        self.mock_trace = Mock(spec=Span)
        self.mock_trace.trace_id = "test-trace-id"
        self.mock_trace.span_id = "test-span-id"

    def test_http_error_with_response_only(self):
        error = HttpError(self.mock_response)
        
        self.assertEqual(error.response, self.mock_response)
        self.assertIsNone(error.trace)
        self.assertIsNone(error.message)
        
        error_str = str(error)
        self.assertIn("HTTP 404", error_str)
        self.assertIn("Not Found", error_str)
        self.assertNotIn("test-trace-id", error_str)

    def test_http_error_with_trace(self):
        error = HttpError(self.mock_response, self.mock_trace)
        
        self.assertEqual(error.response, self.mock_response)
        self.assertEqual(error.trace, self.mock_trace)
        self.assertIsNone(error.message)
        
        error_str = str(error)
        self.assertIn("HTTP 404", error_str)
        self.assertIn("Not Found", error_str)
        self.assertIn("[test-trace-id,test-span-id]", error_str)

    def test_http_error_with_custom_message(self):
        custom_message = "Question 'test-question' not found"
        error = HttpError(self.mock_response, self.mock_trace, custom_message)
        
        self.assertEqual(error.response, self.mock_response)
        self.assertEqual(error.trace, self.mock_trace)
        self.assertEqual(error.message, custom_message)
        
        error_str = str(error)
        self.assertIn(custom_message, error_str)
        self.assertIn("HTTP 404", error_str)
        self.assertIn("Not Found", error_str)
        self.assertIn("[test-trace-id,test-span-id]", error_str)
        self.assertIn("Question 'test-question' not found - HTTP 404", error_str)

    def test_http_error_empty_response_text(self):
        self.mock_response.text = "   "  # Whitespace only
        error = HttpError(self.mock_response, self.mock_trace)
        
        error_str = str(error)
        self.assertIn("HTTP 404", error_str)
        self.assertIn("(empty response)", error_str)

    def test_client_error_inherits_properly(self):
        error = ClientError(self.mock_response, self.mock_trace, "Client error message")
        
        self.assertIsInstance(error, HttpError)
        self.assertIsInstance(error, ClientError)
        
        self.assertEqual(error.response, self.mock_response)
        self.assertEqual(error.trace, self.mock_trace)
        self.assertEqual(error.message, "Client error message")
        
        error_str = str(error)
        self.assertIn("Client error message", error_str)
        self.assertIn("HTTP 404", error_str)
        self.assertIn("Client error message - HTTP 404", error_str)

    def test_backwards_compatibility_without_message(self):
        error = ClientError(self.mock_response, self.mock_trace)
        
        error_str = str(error)
        self.assertIn("HTTP 404", error_str)
        self.assertIn("Not Found", error_str)
        self.assertNotIn(" - HTTP", error_str)  # The dash separator shouldn't be there

    def test_error_args_access(self):
        error = HttpError(self.mock_response, self.mock_trace, "Custom message")
        
        self.assertEqual(len(error.args), 3)
        self.assertEqual(error.args[0], self.mock_response)
        self.assertEqual(error.args[1], self.mock_trace)
        self.assertEqual(error.args[2], "Custom message")
