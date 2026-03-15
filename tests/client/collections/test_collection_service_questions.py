from unittest.mock import Mock, MagicMock, patch
from dnastack.client.collections.client import CollectionServiceClient
from dnastack.client.collections.model import Question
from dnastack.client.models import ServiceEndpoint


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
