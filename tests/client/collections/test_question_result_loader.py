from unittest.mock import Mock, MagicMock
import pytest
from dnastack.client.collections.client import QuestionQueryResultLoader
from dnastack.client.result_iterator import InactiveLoaderError
from dnastack.common.tracing import Span


def test_loader_initialization():
    """Test QuestionQueryResultLoader initialization"""
    mock_session = Mock()
    trace = Span()

    loader = QuestionQueryResultLoader(
        service_url="http://test.com/query",
        http_session=mock_session,
        request_payload={"params": {"x": "1"}},
        trace=trace
    )

    assert loader.has_more() is True


def test_loader_has_more_after_load():
    """Test has_more after loading results"""
    mock_session = MagicMock()
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"id": "1"}],
        "pagination": None
    }
    mock_session.__enter__.return_value.post.return_value = mock_response

    loader = QuestionQueryResultLoader(
        service_url="http://test.com/query",
        http_session=mock_session,
        request_payload={"params": {}},
        trace=None
    )

    results = loader.load()

    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert loader.has_more() is False


def test_loader_pagination():
    """Test QuestionQueryResultLoader follows pagination"""
    mock_session = MagicMock()

    # First response with next_page_url
    first_response = Mock()
    first_response.json.return_value = {
        "data": [{"id": "1"}, {"id": "2"}],
        "pagination": {"next_page_url": "http://test.com/page2"}
    }

    # Second response without next_page_url
    second_response = Mock()
    second_response.json.return_value = {
        "data": [{"id": "3"}],
        "pagination": None
    }

    mock_session.__enter__.return_value.post.return_value = first_response
    mock_session.__enter__.return_value.get.return_value = second_response

    loader = QuestionQueryResultLoader(
        service_url="http://test.com/query",
        http_session=mock_session,
        request_payload={"params": {"x": "1"}},
        trace=None
    )

    # Load first page
    page1 = loader.load()
    assert len(page1) == 2
    assert loader.has_more() is True

    # Load second page
    page2 = loader.load()
    assert len(page2) == 1
    assert loader.has_more() is False


def test_loader_raises_inactive_error_when_exhausted():
    """Test that InactiveLoaderError is raised when no more results"""
    mock_session = MagicMock()
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"id": "1"}],
        "pagination": None
    }
    mock_session.__enter__.return_value.post.return_value = mock_response

    loader = QuestionQueryResultLoader(
        service_url="http://test.com/query",
        http_session=mock_session,
        request_payload={"params": {}},
        trace=None
    )

    loader.load()  # First load succeeds

    with pytest.raises(InactiveLoaderError):
        loader.load()  # Second load should raise
