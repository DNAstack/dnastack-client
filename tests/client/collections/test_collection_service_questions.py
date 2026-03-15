from unittest.mock import Mock, MagicMock, patch
import pytest
from dnastack.client.collections.client import CollectionServiceClient, UnknownCollectionError
from dnastack.client.collections.model import Question
from dnastack.client.models import ServiceEndpoint
from dnastack.http.session import ClientError


def test_list_questions_success():
    """Test list_questions returns list of Question objects"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.json.return_value = {
        "items": [
            {
                "id": "q1",
                "name": "Question 1",
                "collection_id": "coll1",
                "parameters": []
            },
            {
                "id": "q2",
                "name": "Question 2",
                "collection_id": "coll1",
                "description": "Test question",
                "parameters": [
                    {"name": "x", "input_type": "STRING", "required": True}
                ]
            }
        ]
    }

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.return_value = mock_response
        mock_session_creator.return_value = mock_session

        questions = client.list_questions("coll1")

    assert len(questions) == 2
    assert isinstance(questions[0], Question)
    assert questions[0].id == "q1"
    assert questions[0].name == "Question 1"
    assert questions[1].id == "q2"
    assert len(questions[1].parameters) == 1


def test_list_questions_empty():
    """Test list_questions with no questions"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.json.return_value = {"items": []}

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.return_value = mock_response
        mock_session_creator.return_value = mock_session

        questions = client.list_questions("coll1")

    assert questions == []


def test_list_questions_with_camel_case_api_response():
    """Test list_questions properly parses camelCase API response"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.json.return_value = {
        "items": [
            {
                "id": "q1",
                "name": "Question with Parameter",
                "collectionId": "coll1",
                "description": "A question",
                "parameters": [
                    {
                        "name": "sample_id",
                        "inputType": "STRING",
                        "required": True,
                        "defaultValue": "SAM001",
                        "label": "Sample ID"
                    }
                ]
            }
        ]
    }

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.return_value = mock_response
        mock_session_creator.return_value = mock_session

        questions = client.list_questions("coll1")

    assert len(questions) == 1
    assert questions[0].id == "q1"
    assert questions[0].collection_id == "coll1"
    assert questions[0].parameters[0].input_type == "STRING"
    assert questions[0].parameters[0].default_value == "SAM001"


def test_list_questions_collection_not_found():
    """Test list_questions raises UnknownCollectionError for 404"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.status_code = 404
    error = ClientError(mock_response, None, "Not found")

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.side_effect = error
        mock_session_creator.return_value = mock_session

        with pytest.raises(UnknownCollectionError):
            client.list_questions("nonexistent")


def test_list_questions_other_error():
    """Test list_questions raises ClientError for other errors"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.status_code = 500
    error = ClientError(mock_response, None, "Server error")

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.side_effect = error
        mock_session_creator.return_value = mock_session

        with pytest.raises(ClientError):
            client.list_questions("coll1")


def test_get_question_success():
    """Test get_question returns Question object"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.json.return_value = {
        "id": "variant_lookup",
        "name": "Variant Lookup",
        "description": "Look up variants",
        "collection_id": "my-variants",
        "parameters": [
            {"name": "chromosome", "input_type": "STRING", "required": True},
            {"name": "position", "input_type": "INTEGER", "required": True}
        ]
    }

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.return_value = mock_response
        mock_session_creator.return_value = mock_session

        question = client.get_question("my-variants", "variant_lookup")

    assert isinstance(question, Question)
    assert question.id == "variant_lookup"
    assert question.name == "Variant Lookup"
    assert question.description == "Look up variants"
    assert len(question.parameters) == 2
    assert question.parameters[0].name == "chromosome"
    assert question.parameters[0].required is True


def test_get_question_not_found():
    """Test get_question raises UnknownCollectionError for 404"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.status_code = 404
    error = ClientError(mock_response, None, "Not found")

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.side_effect = error
        mock_session_creator.return_value = mock_session

        with pytest.raises(UnknownCollectionError):
            client.get_question("nonexistent", "q1")


def test_get_question_other_error():
    """Test get_question raises ClientError for other errors"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.status_code = 500
    error = ClientError(mock_response, None, "Server error")

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.get.side_effect = error
        mock_session_creator.return_value = mock_session

        with pytest.raises(ClientError):
            client.get_question("coll1", "q1")


def test_ask_question_returns_iterator():
    """Test ask_question returns ResultIterator"""
    from dnastack.client.result_iterator import ResultIterator

    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session_creator.return_value = mock_session

        result = client.ask_question(
            "my-collection",
            "my-question",
            {"param1": "value1"}
        )

    assert isinstance(result, ResultIterator)


def test_ask_question_executes_query():
    """Test ask_question makes correct API call"""
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    client = CollectionServiceClient(endpoint)

    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"id": "1", "value": "result"}],
        "pagination": None
    }

    with patch.object(client, 'create_http_session') as mock_session_creator:
        mock_session = MagicMock()
        mock_session.__enter__.return_value.post.return_value = mock_response
        mock_session_creator.return_value = mock_session

        result_iter = client.ask_question(
            "test-coll",
            "test-q",
            {"x": "1", "y": "2"}
        )

        # Consume iterator
        results = list(result_iter)

    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert results[0]["value"] == "result"
