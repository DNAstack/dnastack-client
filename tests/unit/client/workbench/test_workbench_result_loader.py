"""Unit tests for WorkbenchResultLoader parameter serialization"""
import unittest
from unittest.mock import Mock, MagicMock

from dnastack.client.workbench.base_client import WorkbenchResultLoader
from dnastack.client.workbench.models import BaseListOptions, PaginatedResource, Pagination


class StubPaginatedResource(PaginatedResource):
    """PaginatedResource subclass that returns an empty items list."""
    data: list = []

    def items(self):
        return self.data


class StubResultLoader(WorkbenchResultLoader):
    """Concrete subclass for testing, since WorkbenchResultLoader.extract_api_response is abstract-like."""

    def extract_api_response(self, response_body: dict) -> PaginatedResource:
        return StubPaginatedResource(
            pagination=Pagination(
                next_page_url=response_body.get('next_page_url'),
                total_elements=response_body.get('total_elements', 0),
            ),
            data=response_body.get('items', []),
        )


class TestWorkbenchResultLoaderParams(unittest.TestCase):
    """Test that WorkbenchResultLoader excludes None values from query params on the first request."""

    def _make_mock_session(self, response_body: dict):
        mock_session = MagicMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{}'
        mock_response.json.return_value = response_body
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_session.get.return_value = mock_response
        return mock_session

    def test_first_request_excludes_none_params(self):
        """params dict sent to session.get() must not contain any None values."""
        mock_session = self._make_mock_session({'next_page_url': None, 'total_elements': 0})

        list_options = BaseListOptions(page=2, page_size=5)
        loader = StubResultLoader(
            service_url='https://example.com/api/runs',
            http_session=mock_session,
            trace=None,
            list_options=list_options,
            max_results=10,
        )

        loader.load()

        mock_session.get.assert_called_once()
        call_kwargs = mock_session.get.call_args
        params = call_kwargs.kwargs.get('params') or call_kwargs[1].get('params')

        # Must be a plain dict, not a Pydantic model
        self.assertIsInstance(params, dict)

        # No None values allowed
        none_keys = [k for k, v in params.items() if v is None]
        self.assertEqual(none_keys, [], f"params contains None values for keys: {none_keys}")

        # The explicitly-set values must be present
        self.assertEqual(params['page'], 2)
        self.assertEqual(params['page_size'], 5)

        # page_token was not set, so it must be absent entirely
        self.assertNotIn('page_token', params)

    def test_default_options_produce_empty_params(self):
        """When no options are explicitly set, params dict should be empty (all defaults are None)."""
        mock_session = self._make_mock_session({'next_page_url': None, 'total_elements': 0})

        loader = StubResultLoader(
            service_url='https://example.com/api/runs',
            http_session=mock_session,
            trace=None,
            list_options=BaseListOptions(),
            max_results=10,
        )

        loader.load()

        call_kwargs = mock_session.get.call_args
        params = call_kwargs.kwargs.get('params') or call_kwargs[1].get('params')
        self.assertIsInstance(params, dict)
        self.assertEqual(params, {})


if __name__ == '__main__':
    unittest.main()
