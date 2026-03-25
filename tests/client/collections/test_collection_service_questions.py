from unittest.mock import Mock, MagicMock, patch
import pytest
from dnastack.client.collections.client import CollectionServiceClient, UnknownCollectionError
from dnastack.client.collections.model import Question
from dnastack.client.models import ServiceEndpoint
from dnastack.http.session import ClientError


@pytest.fixture
def client():
    endpoint = ServiceEndpoint(url="http://test.com/collections/")
    return CollectionServiceClient(endpoint)


def make_mock_session(client, *, get=None, post=None, side_effect=None):
    """Patch create_http_session on client with a mock that returns get/post responses."""
    mock_session = MagicMock()
    if side_effect:
        mock_session.__enter__.return_value.get.side_effect = side_effect
        mock_session.__enter__.return_value.post.side_effect = side_effect
    if get:
        mock_session.__enter__.return_value.get.return_value = get
    if post:
        mock_session.__enter__.return_value.post.return_value = post
    return patch.object(client, 'create_http_session', return_value=mock_session)


def test_list_questions_success(client):
    """Test list_questions returns list of Question objects"""
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

    with make_mock_session(client, get=mock_response):
        questions = client.list_questions("coll1")

    assert len(questions) == 2
    assert isinstance(questions[0], Question)
    assert questions[0].id == "q1"
    assert questions[0].name == "Question 1"
    assert questions[1].id == "q2"
    assert len(questions[1].parameters) == 1


def test_list_questions_empty(client):
    """Test list_questions with no questions"""
    mock_response = Mock()
    mock_response.json.return_value = {"items": []}

    with make_mock_session(client, get=mock_response):
        questions = client.list_questions("coll1")

    assert questions == []


def test_list_questions_with_camel_case_api_response(client):
    """Test list_questions properly parses camelCase API response"""
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

    with make_mock_session(client, get=mock_response):
        questions = client.list_questions("coll1")

    assert len(questions) == 1
    assert questions[0].id == "q1"
    assert questions[0].collection_id == "coll1"
    assert questions[0].parameters[0].input_type == "STRING"
    assert questions[0].parameters[0].default_value == "SAM001"


def test_list_questions_collection_not_found(client):
    """Test list_questions raises UnknownCollectionError for 404"""
    mock_response = Mock()
    mock_response.status_code = 404
    error = ClientError(mock_response, None, "Not found")

    with make_mock_session(client, side_effect=error):
        with pytest.raises(UnknownCollectionError):
            client.list_questions("nonexistent")


def test_list_questions_other_error(client):
    """Test list_questions raises ClientError for other errors"""
    mock_response = Mock()
    mock_response.status_code = 500
    error = ClientError(mock_response, None, "Server error")

    with make_mock_session(client, side_effect=error):
        with pytest.raises(ClientError):
            client.list_questions("coll1")


def test_get_question_success(client):
    """Test get_question returns Question object"""
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

    with make_mock_session(client, get=mock_response):
        question = client.get_question("my-variants", "variant_lookup")

    assert isinstance(question, Question)
    assert question.id == "variant_lookup"
    assert question.name == "Variant Lookup"
    assert question.description == "Look up variants"
    assert len(question.parameters) == 2
    assert question.parameters[0].name == "chromosome"
    assert question.parameters[0].required is True


def test_get_question_not_found(client):
    """Test get_question raises UnknownCollectionError for 404"""
    mock_response = Mock()
    mock_response.status_code = 404
    error = ClientError(mock_response, None, "Not found")

    with make_mock_session(client, side_effect=error):
        with pytest.raises(UnknownCollectionError):
            client.get_question("nonexistent", "q1")


def test_get_question_other_error(client):
    """Test get_question raises ClientError for other errors"""
    mock_response = Mock()
    mock_response.status_code = 500
    error = ClientError(mock_response, None, "Server error")

    with make_mock_session(client, side_effect=error):
        with pytest.raises(ClientError):
            client.get_question("coll1", "q1")


def test_ask_question_executes_query(client):
    """Test ask_question makes correct API call"""
    mock_response = Mock()
    mock_response.json.return_value = {
        "data": [{"id": "1", "value": "result"}],
        "pagination": None
    }

    with make_mock_session(client, post=mock_response):
        result_iter = client.ask_question(
            "test-coll",
            "test-q",
            {"x": "1", "y": "2"}
        )
        results = list(result_iter)

    assert len(results) == 1
    assert results[0]["id"] == "1"
    assert results[0]["value"] == "result"
