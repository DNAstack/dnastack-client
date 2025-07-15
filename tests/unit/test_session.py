import unittest
from unittest.mock import Mock
from requests import Response

from dnastack.http.session import HttpError, ClientError
from dnastack.common.tracing import Span


class TestSession(unittest.TestCase):

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


if __name__ == '__main__':
    unittest.main()